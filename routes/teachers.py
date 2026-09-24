from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
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
    class_ids: Optional[List[int]] = []


# ═══════════════════════════════════════════════════════════════
#  MY CLASSES — Logged-in teacher ki assigned classes
#  ⚠️ IMPORTANT: Ye endpoint dynamic routes se PEHLE hona chahiye
# ═══════════════════════════════════════════════════════════════
@router.get("/my-classes")
def get_my_classes(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Logged-in teacher ki assigned classes."""
    user_id = current_user.get("user_id") or current_user.get("id")
    
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    try:
        # Teacher ID dhundo
        cursor.execute(
            "SELECT id FROM teachers WHERE user_id = %s AND deleted_at IS NULL",
            (user_id,)
        )
        teacher = cursor.fetchone()
        
        if not teacher:
            return []
        
        teacher_id = teacher["id"]
        
        # Assigned classes nikalo
        cursor.execute(
            """SELECT DISTINCT
                c.id,
                c.name
               FROM teacher_assignments ta
               JOIN classes c ON c.id = ta.class_id
               WHERE ta.teacher_id = %s AND ta.school_id = %s
               ORDER BY c.name""",
            (teacher_id, school_id)
        )
        rows = cursor.fetchall()
        
        return [{"id": r["id"], "name": r["name"]} for r in rows]
        
    except Exception as e:
        print(f"my-classes error: {e}")
        return []
    finally:
        conn.close()


# ============ TEACHER + USER + CLASSES ============
@router.post("/create-with-user", status_code=201)
def create_teacher_with_user(
    data: TeacherWithUserCreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher + User + Class Assignments ek saath banao."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        hashed_password = hash_password(data.password)
        cursor.execute(
            """INSERT INTO users (full_name, email, password, role, school_id, phone) 
               VALUES (%s, %s, %s, 'teacher', %s, %s) RETURNING id""",
            (data.full_name, data.email, hashed_password, school_id, data.phone)
        )
        user_id = cursor.fetchone()["id"]

        cursor.execute(
            """INSERT INTO teachers (user_id, qualification, school_id) 
               VALUES (%s, %s, %s) RETURNING id""",
            (user_id, data.qualification, school_id)
        )
        teacher_id = cursor.fetchone()["id"]

        assigned_classes = []
        if data.class_ids:
            for class_id in data.class_ids:
                try:
                    cursor.execute(
                        "SELECT id FROM classes WHERE id = %s AND school_id = %s",
                        (class_id, school_id)
                    )
                    if not cursor.fetchone():
                        continue

                    cursor.execute(
                        """INSERT INTO teacher_assignments 
                           (teacher_id, class_id, school_id) 
                           VALUES (%s, %s, %s) RETURNING id""",
                        (teacher_id, class_id, school_id)
                    )
                    assigned_classes.append(class_id)
                except Exception as e:
                    print(f"Class assignment failed for class {class_id}: {e}")

        conn.commit()

        return {
            "id": teacher_id,
            "user_id": user_id,
            "full_name": data.full_name,
            "email": data.email,
            "qualification": data.qualification,
            "phone": data.phone,
            "assigned_classes": assigned_classes,
            "message": f"Teacher {data.full_name} created with {len(assigned_classes)} class(es)!"
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ Get Teacher Classes (Admin) ============
@router.get("/{teacher_id}/classes")
def get_teacher_classes(
    teacher_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Ek teacher ki assigned classes nikalo — admin ke liye."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute(
            """SELECT ta.id, ta.class_id, c.name AS class_name
               FROM teacher_assignments ta
               JOIN classes c ON c.id = ta.class_id
               WHERE ta.teacher_id = %s AND ta.school_id = %s
               ORDER BY c.name""",
            (teacher_id, school_id)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Get teacher classes error: {e}")
        return []
    finally:
        conn.close()


# ============ Update Teacher Classes ============
@router.put("/{teacher_id}/classes")
def update_teacher_classes(
    teacher_id: int,
    data: dict,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Teacher ki classes update karo."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can update")

    class_ids = data.get("class_ids", [])
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute(
            "DELETE FROM teacher_assignments WHERE teacher_id = %s AND school_id = %s",
            (teacher_id, school_id)
        )

        assigned = []
        for class_id in class_ids:
            cursor.execute(
                """INSERT INTO teacher_assignments 
                   (teacher_id, class_id, school_id) 
                   VALUES (%s, %s, %s) RETURNING id""",
                (teacher_id, class_id, school_id)
            )
            assigned.append(class_id)

        conn.commit()

        return {
            "message": f"Updated to {len(assigned)} class(es)",
            "assigned_classes": assigned
        }
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
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can edit")

    result = update_teacher(teacher_id, teacher_data.qualification, school_id)
    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
    teacher_record = cursor.fetchone()

    if teacher_record:
        user_id = teacher_record["user_id"]

        full_name = getattr(teacher_data, "full_name", None)
        if full_name:
            cursor.execute("UPDATE users SET full_name = %s WHERE id = %s", (full_name, user_id))

        email = getattr(teacher_data, "email", None)
        if email:
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=400, detail="Email already exists")
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))

        phone = getattr(teacher_data, "phone", None)
        if phone:
            cursor.execute("UPDATE users SET phone = %s WHERE id = %s", (phone, user_id))

        password = getattr(teacher_data, "password", None)
        if password and len(password) >= 8:
            from services.auth_service import hash_password
            hashed = hash_password(password)
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))

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