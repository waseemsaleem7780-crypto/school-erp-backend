from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.schemas import teacherscreate
from services.teacher_service import (
    create_teacher,
    get_all_teachers,
    update_teacher,
    delete_teacher,
    restore_teacher,
)
from services.auth_service import hash_password
from utils.dependencies import get_current_user, get_current_school_id
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# ============ SCHEMA ============
class TeacherWithUserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    qualification: str
    phone: Optional[str] = None


# ============ NAYA ENDPOINT: User + Teacher ek saath ============
@router.post("/create-with-user", status_code=201)
def create_teacher_with_user(
    data: TeacherWithUserCreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher + User ek saath banao (1 click)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. Check email unique
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 2. User banao (teacher role)
        hashed_password = hash_password(data.password)
        cursor.execute(
            """INSERT INTO users (full_name, email, password, role, school_id, phone) 
               VALUES (%s, %s, %s, 'teacher', %s, %s) RETURNING id""",
            (data.full_name, data.email, hashed_password, school_id, data.phone)
        )
        user_id = cursor.fetchone()["id"]

        # 3. Teacher record banao
        cursor.execute(
            """INSERT INTO teachers (user_id, qualification, school_id) 
               VALUES (%s, %s, %s) RETURNING id""",
            (user_id, data.qualification, school_id)
        )
        teacher_id = cursor.fetchone()["id"]

        conn.commit()

        return {
            "id": teacher_id,
            "user_id": user_id,
            "full_name": data.full_name,
            "email": data.email,
            "qualification": data.qualification,
            "phone": data.phone,
            "message": f"Teacher {data.full_name} created successfully!"
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ Existing Endpoints ============
@router.post("/", status_code=201)
def add_teacher(
    teacher_data: teacherscreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    result = create_teacher(
        teacher_data.user_id,
        teacher_data.qualification,
        school_id
    )

    # Phone update
    phone = getattr(teacher_data, "phone", None)
    if phone:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            "UPDATE users SET phone = %s WHERE id = %s",
            (phone, teacher_data.user_id)
        )
        conn.commit()
        conn.close()

    return result


@router.get("/")
def get_teachers(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_all_teachers(school_id)


@router.put("/{teacher_id}")
def edit_teacher(
    teacher_id: int,
    teacher_data: teacherscreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher edit — qualification, phone, aur password (optional) bhi update hoga."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can edit")

    # 1. Teacher record update karo (qualification)
    result = update_teacher(teacher_id, teacher_data.qualification, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 2. User info update karo (phone, password)
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Teacher ka user_id dhundo
    cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
    teacher_record = cursor.fetchone()

    if teacher_record:
        user_id = teacher_record["user_id"]

        # Phone update (agar diya hai)
        phone = getattr(teacher_data, "phone", None)
        if phone:
            cursor.execute(
                "UPDATE users SET phone = %s WHERE id = %s",
                (phone, user_id)
            )

        # ✅ Password update (agar diya hai — Optional)
        password = getattr(teacher_data, "password", None)
        if password and len(password) >= 8:
            hashed = hash_password(password)
            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed, user_id)
            )

    conn.commit()
    conn.close()

    return result


@router.delete("/{teacher_id}")
def remove_teacher(
    teacher_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_teacher(teacher_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return result


@router.post("/{teacher_id}/restore")
def restore_deleted_teacher(
    teacher_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can restore")

    result = restore_teacher(teacher_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found or not deleted")

    return result