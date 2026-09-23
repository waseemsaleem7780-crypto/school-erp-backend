from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from models.schemas import homeworkcreate
from services.homework_service import (
    create_homework,
    get_homework_by_student,
    get_homework_by_class,
)
from utils.dependencies import get_current_user
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/homework", tags=["Homework"])


# ═══════════════════════════════════════════════════════════════
#  SCHEMA — teacher_id hata diya (JWT se aayega)
# ═══════════════════════════════════════════════════════════════

class BulkHomeworkCreate(BaseModel):
    class_id: int
    subject_id: int
    # teacher_id: int  ← ❌ Hata diya — JWT se aayega
    title: str
    description: str
    deadline: str
    student_ids: Optional[List[int]] = None  # None = all students in class


# ═══════════════════════════════════════════════════════════════
#  HELPER — JWT se teacher_id nikalo
# ═══════════════════════════════════════════════════════════════

def get_teacher_id_from_jwt(current_user: dict) -> int:
    """Logged-in user ka teacher_id nikalo. Agar teacher record nahi to error."""
    user_id = current_user.get("user_id") or current_user.get("id")
    role = current_user.get("role")

    # Super admin ya admin ke liye fallback
    if role in ["super_admin", "admin"]:
        # Admin apna teacher record na ho to error
        pass

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        "SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL",
        (user_id,)
    )
    teacher = cursor.fetchone()
    conn.close()

    if not teacher:
        raise HTTPException(
            status_code=400,
            detail="Aap ka teacher record nahi mila. Admin se contact karo."
        )

    return teacher["id"]


# ═══════════════════════════════════════════════════════════════
#  SINGLE HOMEWORK — POST /
# ═══════════════════════════════════════════════════════════════

@router.post("/", status_code=201)
def add_homework(
    hw_data: homeworkcreate,
    current_user: dict = Depends(get_current_user)
):
    """Single student ko homework assign karo."""
    # ✅ Teacher ID JWT se
    teacher_id = get_teacher_id_from_jwt(current_user)

    result = create_homework(
        hw_data.student_id,
        hw_data.subject_id,
        teacher_id,             # ✅ JWT se
        hw_data.title,
        hw_data.description,
        hw_data.deadline
    )
    return result


# ═══════════════════════════════════════════════════════════════
#  BULK HOMEWORK — POST /bulk
# ═══════════════════════════════════════════════════════════════

@router.post("/bulk", status_code=201)
def add_bulk_homework(
    data: BulkHomeworkCreate,
    current_user: dict = Depends(get_current_user)
):
    """Ek hi baar mein poori class ko homework assign karo."""
    # ✅ Teacher ID JWT se — frontend se nahi
    teacher_id = get_teacher_id_from_jwt(current_user)

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # Agar student_ids nahi diye — poori class ke students lo
        target_ids = data.student_ids
        if not target_ids:
            cursor.execute(
                "SELECT id FROM students WHERE class_id = %s AND deleted_at IS NULL",
                (data.class_id,)
            )
            target_ids = [r["id"] for r in cursor.fetchall()]

        if not target_ids:
            raise HTTPException(status_code=400, detail="Is class mein koi student nahi")

        # ✅ Subject validate karo
        cursor.execute(
            "SELECT id FROM subjects WHERE id = %s",
            (data.subject_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Subject not found")

        # Ek hi transaction mein saare insert karo
        inserted = []
        for sid in target_ids:
            cursor.execute(
                """INSERT INTO homework 
                   (student_id, subject_id, teacher_id, title, description, deadline) 
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (sid, data.subject_id, teacher_id, data.title, data.description, data.deadline)
            )
            inserted.append(cursor.fetchone()["id"])

        conn.commit()

        return {
            "message": f"Homework assigned to {len(inserted)} students",
            "count": len(inserted),
            "ids": inserted,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Bulk homework error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
#  GET HOMEWORK — Per Student / Per Class
# ═══════════════════════════════════════════════════════════════

@router.get("/student/{student_id}")
def get_homework(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Ek student ki saari homework."""
    return get_homework_by_student(student_id)


@router.get("/class/{class_id}")
def get_homework_class(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Class ki saari homework (poori class)."""
    return get_homework_by_class(class_id)