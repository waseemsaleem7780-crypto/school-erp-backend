from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.whatsapp_service import send_whatsapp
from utils.dependencies import get_current_user, get_current_school_id
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/teacher-message", tags=["Teacher Message"])


class TeacherMessageRequest(BaseModel):
    student_id: int
    message: str


@router.get("/my-classes")
def my_classes(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher ki assigned classes."""
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # ✅ deleted_at filter HATAO
    cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        print(f"[teacher-message] Teacher not found for user_id={user_id}")
        return []

    teacher_id = teacher["id"]

    cursor.execute(
        """SELECT 
               ta.id, ta.class_id, c.name as class_name,
               ta.section_id, s.name as section_name,
               ta.subject_id, sub.name as subject_name,
               ta.is_class_teacher
           FROM teacher_assignments ta
           JOIN classes c ON c.id = ta.class_id
           LEFT JOIN sections s ON s.id = ta.section_id
           LEFT JOIN subjects sub ON sub.id = ta.subject_id
           WHERE ta.teacher_id = %s AND ta.school_id = %s
           ORDER BY c.name, s.name""",
        (teacher_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/students/{class_id}")
def get_students(
    class_id: int,
    section_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Us class ke students — sirf agar teacher assigned hai."""
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # ✅ deleted_at filter HATAO
    cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        raise HTTPException(404, "Teacher not found")
    teacher_id = teacher["id"]

    cursor.execute(
        """SELECT 1 FROM teacher_assignments 
           WHERE teacher_id = %s AND class_id = %s AND school_id = %s
             AND (section_id IS NULL OR section_id = %s) LIMIT 1""",
        (teacher_id, class_id, school_id, section_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(403, "You are not assigned to this class")

    query = """
        SELECT s.id, s.roll_number, u.full_name as student_name,
               s.parent_whatsapp as parent_phone,
               s.parent_name as parent_name
        FROM students s
        JOIN users u ON u.id = s.user_id
        WHERE s.class_id = %s AND s.school_id = %s
    """
    params = [class_id, school_id]
    if section_id:
        query += " AND s.section_id = %s"
        params.append(section_id)
    query += " ORDER BY s.roll_number"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/send")
def send_teacher_message(
    request: TeacherMessageRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher apne student ke parent ko WhatsApp bheje."""
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # ✅ deleted_at filter HATAO — yahi masla hai
    cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        print(f"[teacher-message/send] Teacher not found for user_id={user_id}")
        raise HTTPException(404, "Teacher not found")
    teacher_id = teacher["id"]

    # Verify teacher is allowed
    cursor.execute(
        """SELECT 1 FROM students st
           JOIN teacher_assignments ta ON ta.class_id = st.class_id
           WHERE st.id = %s AND ta.teacher_id = %s
             AND (ta.section_id IS NULL OR ta.section_id = st.section_id)
           LIMIT 1""",
        (request.student_id, teacher_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(403, "Not allowed to message this student's parent")

    # Parent phone
    cursor.execute(
        """SELECT u.full_name as student_name, s.roll_number,
                  s.parent_whatsapp as parent_phone,
                  s.parent_name as parent_name
           FROM students s
           JOIN users u ON u.id = s.user_id
           WHERE s.id = %s AND s.school_id = %s LIMIT 1""",
        (request.student_id, school_id)
    )
    info = cursor.fetchone()

    if not info or not info["parent_phone"]:
        conn.close()
        raise HTTPException(400, "Parent WhatsApp number not found")

    result = send_whatsapp(school_id, info["parent_phone"], request.message)

    # Log (agar table exist kare)
    try:
        cursor.execute(
            """INSERT INTO teacher_messages 
               (teacher_id, student_id, parent_phone, message, school_id, status, whatsapp_message_id, error_message)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (teacher_id, request.student_id, info["parent_phone"], request.message,
             school_id, "sent" if result["success"] else "failed",
             result.get("message_id"), result.get("error"))
        )
        conn.commit()
    except Exception as e:
        print(f"teacher_messages log failed: {e}")
        conn.rollback()

    conn.close()

    return {
        "success": result["success"],
        "message": "Message sent" if result["success"] else "Failed",
        "parent_name": info["parent_name"],
        "parent_phone": info["parent_phone"],
        "student_name": info["student_name"]
    }


@router.get("/history")
def message_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        return []
    teacher_id = teacher["id"]

    try:
        cursor.execute(
            """SELECT tm.id, tm.message, tm.status, tm.sent_at,
                      u.full_name as student_name, s.roll_number
               FROM teacher_messages tm
               JOIN students s ON s.id = tm.student_id
               JOIN users u ON u.id = s.user_id
               WHERE tm.teacher_id = %s
               ORDER BY tm.sent_at DESC LIMIT %s""",
            (teacher_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"history error: {e}")
        conn.close()
        return []