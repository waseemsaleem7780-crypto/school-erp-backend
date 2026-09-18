from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.schemas import students
from services.student_service import (
    create_student,
    get_students_by_class,
    get_all_students,
    update_student,
    delete_student,
    restore_student,
    get_deleted_students,
)
from services.auth_service import hash_password
from database.db import get_db_connection, get_dict_cursor
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/students", tags=["Students"])


# ============ SCHEMA ============
class StudentWithUserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    roll_number: str
    class_id: int
    section_id: int
    phone: Optional[str] = None


# ============ NAYA ENDPOINT: User + Student ek saath ============
@router.post("/create-with-user", status_code=201)
def create_student_with_user(
    data: StudentWithUserCreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Student + User ek saath banao (1 click)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. Check email unique
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 2. User banao (student role)
        hashed_password = hash_password(data.password)
        cursor.execute(
            """INSERT INTO users (full_name, email, password, role, school_id, phone) 
               VALUES (%s, %s, %s, 'student', %s, %s) RETURNING id""",
            (data.full_name, data.email, hashed_password, school_id, data.phone)
        )
        user_id = cursor.fetchone()["id"]

        # 3. Student record banao
        cursor.execute(
            """INSERT INTO students (user_id, roll_number, class_id, section_id, school_id) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (user_id, data.roll_number, data.class_id, data.section_id, school_id)
        )
        student_id = cursor.fetchone()["id"]

        conn.commit()

        return {
            "id": student_id,
            "user_id": user_id,
            "full_name": data.full_name,
            "email": data.email,
            "roll_number": data.roll_number,
            "class_id": data.class_id,
            "section_id": data.section_id,
            "phone": data.phone,
            "message": f"Student {data.full_name} created successfully!"
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ Existing Endpoints (Same Rehte Hain) ============
@router.post("/", status_code=201)
def add_student(
    student_data: students,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    result = create_student(
        student_data.user_id,
        student_data.roll_number,
        student_data.class_id,
        student_data.section_id,
        school_id
    )
    return result


@router.get("/")
def get_all(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_all_students(school_id)


@router.get("/deleted")
def get_deleted(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can view deleted")
    return get_deleted_students(school_id)


@router.get("/class/{class_id}")
def get_students_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, roll_number, class_id, section_id 
           FROM students 
           WHERE class_id = %s AND school_id = %s AND deleted_at IS NULL 
           ORDER BY roll_number""",
        (class_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/class/{class_id}/section/{section_id}")
def get_students_for_class_section(
    class_id: int,
    section_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, roll_number, class_id, section_id 
           FROM students 
           WHERE class_id = %s AND section_id = %s AND school_id = %s AND deleted_at IS NULL 
           ORDER BY roll_number""",
        (class_id, section_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{class_id}")
def get_students(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_students_by_class(class_id, school_id)


@router.put("/{student_id}")
def edit_student(
    student_id: int,
    student_data: students,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can edit")

    result = update_student(
        student_id,
        student_data.roll_number,
        student_data.class_id,
        student_data.section_id,
        school_id
    )

    if not result:
        raise HTTPException(status_code=404, detail="Student not found")

    return result


@router.delete("/{student_id}")
def remove_student(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_student(student_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Student not found")

    return result


@router.post("/{student_id}/restore")
def restore_deleted_student(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can restore")

    result = restore_student(student_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Student not found or not deleted")

    return result