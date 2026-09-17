from fastapi import APIRouter, Depends, HTTPException
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
from database.db import get_db_connection, get_dict_cursor
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/students", tags=["Students"])


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
    """Soft-deleted students ki list."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can view deleted")
    return get_deleted_students(school_id)


# ⚠️ IMPORTANT: Ye routes /{class_id} se PEHLE hone chahiye
@router.get("/class/{class_id}")
def get_students_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Ek class ke saare students (Attendance page ke liye)."""
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
    """Ek class + section ke students (Attendance page ke liye)."""
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


# Ye /{class_id} route LAST mein rakho (warna conflict hoga)
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
    """Soft delete — data safe rehta hai."""
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
    """Soft-deleted student ko restore karo."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can restore")

    result = restore_student(student_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Student not found or not deleted")

    return result