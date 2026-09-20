from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.whatsapp_service import send_whatsapp
from utils.dependencies import get_current_user, get_current_school_id
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/teacher-message", tags=["Teacher Message"])


class TeacherMessageRequest(BaseModel):
    student_id: Optional[int] = None
    class_id: Optional[int] = None
    section_id: Optional[int] = None
    send_to_all: bool = False
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

    cursor.execute("SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL", (user_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
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
    """Us class ke alive students — deleted nahi."""
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        raise HTTPException(404, "Teacher not found")
    teacher_id = teacher["id"]

    # Verify teacher assigned
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
        WHERE s.class_id = %s 
          AND s.school_id = %s
          AND s.deleted_at IS NULL
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
    """Teacher apne student(s) ke parent(s) ko WhatsApp bheje.
    - Single: student_id do
    - Bulk: send_to_all=True + class_id (+ optional section_id) do
    """
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        raise HTTPException(404, "Teacher not found")
    teacher_id = teacher["id"]

    # ══════════════════════════════════════════
    # CASE 1: BULK — poori class ke parents
    # ══════════════════════════════════════════
    if request.send_to_all:
        if not request.class_id:
            conn.close()
            raise HTTPException(400, "class_id required for bulk send")

        # Verify teacher assigned to this class
        cursor.execute(
            """SELECT 1 FROM teacher_assignments 
               WHERE teacher_id = %s AND class_id = %s AND school_id = %s LIMIT 1""",
            (teacher_id, request.class_id, school_id)
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(403, "Not assigned to this class")

        query = """
            SELECT s.id, u.full_name as student_name, s.roll_number,
                   s.parent_whatsapp as parent_phone,
                   s.parent_name as parent_name
            FROM students s
            JOIN users u ON u.id = s.user_id
            WHERE s.class_id = %s 
              AND s.school_id = %s
              AND s.deleted_at IS NULL
              AND s.parent_whatsapp IS NOT NULL
              AND s.parent_whatsapp != ''
        """
        params = [request.class_id, school_id]
        if request.section_id:
            query += " AND s.section_id = %s"
            params.append(request.section_id)

        cursor.execute(query, tuple(params))
        students = cursor.fetchall()

        if not students:
            conn.close()
            raise HTTPException(400, "No students with parent WhatsApp found")

        sent_count = 0
        failed_count = 0
        results = []

        for st in students:
            result = send_whatsapp(school_id, st["parent_phone"], request.message)
            status = "sent" if result.get("success") else "failed"
            if result.get("success"):
                sent_count += 1
            else:
                failed_count += 1

            cursor.execute(
                """INSERT INTO teacher_messages 
                   (teacher_id, student_id, parent_phone, message, school_id, status, whatsapp_message_id, error_message)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (teacher_id, st["id"], st["parent_phone"], request.message,
                 school_id, status, result.get("message_id"), result.get("error"))
            )
            results.append({
                "student": st["student_name"],
                "status": status,
            })

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Message sent to {sent_count} parents ({failed_count} failed)",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total": len(students),
            "results": results,
        }

    # ══════════════════════════════════════════
    # CASE 2: SINGLE — ek student
    # ══════════════════════════════════════════
    if not request.student_id:
        conn.close()
        raise HTTPException(400, "student_id required")

    cursor.execute(
        """SELECT 1 FROM students st
           JOIN teacher_assignments ta ON ta.class_id = st.class_id
           WHERE st.id = %s AND ta.teacher_id = %s
             AND st.deleted_at IS NULL
             AND (ta.section_id IS NULL OR ta.section_id = st.section_id)
           LIMIT 1""",
        (request.student_id, teacher_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(403, "Not allowed to message this student's parent")

    cursor.execute(
        """SELECT u.full_name as student_name, s.roll_number,
                  s.parent_whatsapp as parent_phone,
                  s.parent_name as parent_name
           FROM students s
           JOIN users u ON u.id = s.user_id
           WHERE s.id = %s AND s.school_id = %s AND s.deleted_at IS NULL LIMIT 1""",
        (request.student_id, school_id)
    )
    info = cursor.fetchone()

    if not info or not info["parent_phone"]:
        conn.close()
        raise HTTPException(400, "Parent WhatsApp number not found")

    result = send_whatsapp(school_id, info["parent_phone"], request.message)

    cursor.execute(
        """INSERT INTO teacher_messages 
           (teacher_id, student_id, parent_phone, message, school_id, status, whatsapp_message_id, error_message)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (teacher_id, request.student_id, info["parent_phone"], request.message,
         school_id, "sent" if result.get("success") else "failed",
         result.get("message_id"), result.get("error"))
    )
    conn.commit()
    conn.close()

    return {
        "success": result.get("success"),
        "message": "Message sent" if result.get("success") else "Failed",
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

    cursor.execute("SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL", (user_id,))
    teacher = cursor.fetchone()
    if not teacher:
        conn.close()
        return []
    teacher_id = teacher["id"]

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