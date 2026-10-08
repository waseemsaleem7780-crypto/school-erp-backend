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


def _get_teacher_id(cursor, user_id):
    cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
    t = cursor.fetchone()
    return t["id"] if t else None


@router.get("/my-classes")
def my_classes(
    current_user: dict = Depends(get_current_user),
):
    """Teacher ki classes — timetable se (jo actually exist karti hain)."""
    user_id = current_user.get("user_id") or current_user.get("id")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    teacher_id = _get_teacher_id(cursor, user_id)
    if not teacher_id:
        conn.close()
        print(f"[my-classes] No teacher for user_id={user_id}")
        return []

    cursor.execute(
        """SELECT DISTINCT 
               c.id AS class_id,
               c.name AS class_name,
               sec.id AS section_id,
               sec.name AS section_name
           FROM timetable t
           JOIN classes c ON c.id = t.class_id
           LEFT JOIN sections sec ON sec.id = t.section_id
           WHERE t.teacher_id = %s
           ORDER BY c.name, sec.name""",
        (teacher_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    print(f"[my-classes] teacher_id={teacher_id}, found {len(rows)} classes")
    return [dict(r) for r in rows]


@router.get("/students/{class_id}")
def get_students(
    class_id: int,
    section_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """Us class ke students — section optional."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    query = """
        SELECT s.id, s.roll_number, u.full_name as student_name,
               s.parent_whatsapp as parent_phone,
               s.parent_name as parent_name,
               s.section_id, s.class_id
        FROM students s
        JOIN users u ON u.id = s.user_id
        WHERE s.class_id = %s
    """
    params = [class_id]
    if section_id:
        query += " AND s.section_id = %s"
        params.append(section_id)
    query += " ORDER BY s.roll_number"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    print(f"[students] class_id={class_id}, section_id={section_id}, found {len(rows)}")
    return [dict(r) for r in rows]


@router.post("/send")
def send_teacher_message(
    request: TeacherMessageRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    """Teacher apne student ke parent ko WhatsApp bheje."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        """SELECT u.full_name as student_name, s.roll_number,
                  s.parent_whatsapp as parent_phone,
                  s.parent_name as parent_name
           FROM students s
           JOIN users u ON u.id = s.user_id
           WHERE s.id = %s LIMIT 1""",
        (request.student_id,)
    )
    info = cursor.fetchone()

    if not info or not info["parent_phone"]:
        conn.close()
        raise HTTPException(400, "Parent WhatsApp number not found")

    result = send_whatsapp(school_id, info["parent_phone"], request.message)

    conn.close()
    return {
        "success": result["success"],
        "message": "Message sent" if result["success"] else "Failed",
        "parent_name": info["parent_name"],
        "parent_phone": info["parent_phone"],
        "student_name": info["student_name"],
        "error": result.get("error"),
    }
