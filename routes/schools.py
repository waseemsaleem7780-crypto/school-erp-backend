from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import re
from models.schemas import schoolscreate
from services.school_service import (
    create_school,
    get_all_schools,
    get_school_by_id,
    update_school,
    delete_school,
    get_school_stats,
)
from services.auth_service import hash_password
from database.db import get_db_connection, get_dict_cursor
from utils.dependencies import get_current_user, require_super_admin

router = APIRouter(prefix="/schools", tags=["Schools"])


# ============ SUBDOMAIN VALIDATOR ============
def clean_and_validate_subdomain(v: str) -> str:
    """Subdomain clean aur validate karo."""
    if not v:
        raise ValueError('Subdomain is required')
    
    # Clean: lowercase, no spaces, no dots, only alphanumeric + hyphens
    v = v.lower().strip()
    v = v.replace(' ', '-')
    v = v.replace('.', '')  # Dots hatao
    v = re.sub(r'[^a-z0-9-]', '', v)  # Sirf valid chars
    v = re.sub(r'-+', '-', v)  # Multiple hyphens → single
    v = v.strip('-')  # Start/end hyphens hatao
    
    # Validate
    if len(v) < 3:
        raise ValueError('Subdomain must be at least 3 characters')
    if len(v) > 30:
        raise ValueError('Subdomain must be at most 30 characters')
    
    return v


# ============ SCHEMAS ============
class SchoolWithAdminCreate(BaseModel):
    name: str
    subdomain: str
    admin_name: str
    admin_email: str
    admin_password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: Optional[str] = "trial"
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        return clean_and_validate_subdomain(v)


class SchoolFullSetupCreate(BaseModel):
    name: str
    subdomain: str
    admin_name: str
    admin_email: str
    admin_password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    num_students: int = 100
    num_teachers: int = 30
    num_classes: int = 10
    num_sections: int = 3
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        return clean_and_validate_subdomain(v)


# ============ SCHOOL + ADMIN CREATE ============
@router.post("/with-admin", status_code=201)
def add_school_with_admin(
    data: SchoolWithAdminCreate,
    current_user: dict = Depends(require_super_admin)
):
    """School + Admin user ek saath create karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. Check subdomain unique
        cursor.execute("SELECT id FROM schools WHERE subdomain = %s", (data.subdomain,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Subdomain already exists")

        # 2. Check email unique
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.admin_email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 3. School banao
        cursor.execute(
            """INSERT INTO schools (name, subdomain, admin_email, phone, address, subscription_plan) 
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (data.name, data.subdomain, data.admin_email, data.phone, data.address, data.subscription_plan)
        )
        school_id = cursor.fetchone()["id"]

        # 4. Admin user banao
        hashed_password = hash_password(data.admin_password)
        cursor.execute(
            """INSERT INTO users (full_name, email, password, role, school_id) 
               VALUES (%s, %s, %s, 'admin', %s) RETURNING id""",
            (data.admin_name, data.admin_email, hashed_password, school_id)
        )
        user_id = cursor.fetchone()["id"]

        conn.commit()

        # 5. Login URL banao
        base_url = "https://school-erp-frontend-azure.vercel.app"
        login_url = f"{base_url}/{data.subdomain}/login"

        return {
            "school_id": school_id,
            "user_id": user_id,
            "name": data.name,
            "subdomain": data.subdomain,
            "login_url": login_url,
            "admin_email": data.admin_email,
            "admin_password": data.admin_password,
            "message": f"School created! Login URL: {login_url}"
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ FULL SETUP (1 CLICK) ============
@router.post("/full-setup", status_code=201)
def full_school_setup(
    data: SchoolFullSetupCreate,
    current_user: dict = Depends(require_super_admin)
):
    """School + Admin + Teachers + Classes + Sections + Students — 1 click."""
    import random
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # Check subdomain unique
        cursor.execute("SELECT id FROM schools WHERE subdomain = %s", (data.subdomain,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Subdomain already exists")

        # Check email unique
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.admin_email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 1. School
        cursor.execute(
            """INSERT INTO schools (name, subdomain, admin_email, phone, address, subscription_plan) 
               VALUES (%s, %s, %s, %s, %s, 'trial') RETURNING id""",
            (data.name, data.subdomain, data.admin_email, data.phone, data.address)
        )
        school_id = cursor.fetchone()["id"]

        # 2. Admin
        hashed_admin = hash_password(data.admin_password)
        cursor.execute(
            """INSERT INTO users (full_name, email, password, role, school_id) 
               VALUES (%s, %s, %s, 'admin', %s) RETURNING id""",
            (data.admin_name, data.admin_email, hashed_admin, school_id)
        )

        # 3. Classes
        class_ids = []
        for i in range(1, data.num_classes + 1):
            cursor.execute(
                "INSERT INTO classes (name, school_id) VALUES (%s, %s) RETURNING id",
                (f"Class {i}", school_id)
            )
            class_ids.append(cursor.fetchone()["id"])

        # 4. Sections
        section_ids_by_class = {}
        section_names = ['A', 'B', 'C', 'D', 'E'][:data.num_sections]
        for class_id in class_ids:
            section_ids_by_class[class_id] = []
            for sec_name in section_names:
                cursor.execute(
                    "INSERT INTO sections (name, class_id, school_id) VALUES (%s, %s, %s) RETURNING id",
                    (sec_name, class_id, school_id)
                )
                section_ids_by_class[class_id].append(cursor.fetchone()["id"])

        # 5. Teachers
        teacher_ids = []
        hashed_teacher = hash_password("teacher123")
        for i in range(1, data.num_teachers + 1):
            teacher_email = f"teacher{i}@{data.subdomain}.com"
            cursor.execute(
                """INSERT INTO users (full_name, email, password, role, school_id) 
                   VALUES (%s, %s, %s, 'teacher', %s) RETURNING id""",
                (f"Teacher {i}", teacher_email, hashed_teacher, school_id)
            )
            user_id = cursor.fetchone()["id"]
            cursor.execute(
                "INSERT INTO teachers (user_id, qualification, school_id) VALUES (%s, %s, %s) RETURNING id",
                (user_id, "M.Sc", school_id)
            )
            teacher_ids.append(cursor.fetchone()["id"])

        # 6. Students
        hashed_student = hash_password("student123")
        for i in range(1, data.num_students + 1):
            class_id = random.choice(class_ids)
            section_id = random.choice(section_ids_by_class[class_id])
            student_email = f"student{i}@{data.subdomain}.com"
            cursor.execute(
                """INSERT INTO users (full_name, email, password, role, school_id) 
                   VALUES (%s, %s, %s, 'student', %s) RETURNING id""",
                (f"Student {i}", student_email, hashed_student, school_id)
            )
            user_id = cursor.fetchone()["id"]
            cursor.execute(
                """INSERT INTO students (user_id, roll_number, class_id, section_id, school_id) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, f"{i:03d}", class_id, section_id, school_id)
            )

        conn.commit()

        base_url = "https://school-erp-frontend-azure.vercel.app"
        login_url = f"{base_url}/{data.subdomain}/login"

        return {
            "success": True,
            "school_id": school_id,
            "name": data.name,
            "subdomain": data.subdomain,
            "login_url": login_url,
            "admin_email": data.admin_email,
            "admin_password": data.admin_password,
            "total_classes": data.num_classes,
            "total_sections": data.num_classes * data.num_sections,
            "total_teachers": data.num_teachers,
            "total_students": data.num_students,
            "teacher_default_password": "teacher123",
            "student_default_password": "student123",
            "message": f"School '{data.name}' created with {data.num_teachers} teachers and {data.num_students} students!"
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ GET SCHOOL BY SUBDOMAIN ============
@router.get("/by-subdomain/{subdomain}")
def get_school_by_subdomain(subdomain: str):
    """Subdomain se school dhundo (login page ke liye)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, subdomain, is_active 
           FROM schools 
           WHERE subdomain = %s AND deleted_at IS NULL""",
        (subdomain,)
    )
    school = cursor.fetchone()
    conn.close()

    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    if not school["is_active"]:
        raise HTTPException(status_code=403, detail="School is inactive")

    return dict(school)


# ============ GET ALL SCHOOLS ============
@router.get("/")
def get_schools(current_user: dict = Depends(require_super_admin)):
    return get_all_schools()


# ============ STATS ============
@router.get("/stats")
def school_stats(current_user: dict = Depends(require_super_admin)):
    return get_school_stats()


# ============ ADMIN ACTIVITY ============
@router.get("/admin-activity")
def admin_activity(current_user: dict = Depends(require_super_admin)):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("""
        SELECT 
            u.id, u.full_name, u.email, u.school_id,
            s.name as school_name,
            u.last_login, u.login_count, u.is_active,
            CASE 
                WHEN u.last_login IS NULL THEN 'never'
                WHEN u.last_login > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'active'
                WHEN u.last_login > CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'inactive'
                ELSE 'dormant'
            END as status
        FROM users u
        LEFT JOIN schools s ON s.id = u.school_id
        WHERE u.role = 'admin' AND u.deleted_at IS NULL
        ORDER BY u.last_login DESC NULLS LAST
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"], "full_name": r["full_name"], "email": r["email"],
            "school_id": r["school_id"], "school_name": r["school_name"],
            "last_login": str(r["last_login"]) if r["last_login"] else None,
            "login_count": r["login_count"] or 0,
            "is_active": r["is_active"], "status": r["status"],
        }
        for r in rows
    ]


# ============ FIX EXISTING SUBDOMAINS ============
@router.post("/fix-subdomains")
def fix_subdomains(current_user: dict = Depends(require_super_admin)):
    """Purane galat subdomains ko sahi karo (dots hatao)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    cursor.execute("SELECT id, subdomain FROM schools WHERE subdomain LIKE '%.%'")
    bad_schools = cursor.fetchall()
    
    fixed = []
    for school in bad_schools:
        old = school["subdomain"]
        # Clean karo
        new = old.lower().replace('.', '-')
        new = re.sub(r'[^a-z0-9-]', '', new)
        new = re.sub(r'-+', '-', new)
        new = new.strip('-')
        
        cursor.execute(
            "UPDATE schools SET subdomain = %s WHERE id = %s",
            (new, school["id"])
        )
        fixed.append({"id": school["id"], "old": old, "new": new})
    
    conn.commit()
    conn.close()
    
    return {"fixed_count": len(fixed), "fixed": fixed}


# ============ DYNAMIC ROUTES (LAST) ============
@router.get("/{school_id}")
def get_school(
    school_id: int,
    current_user: dict = Depends(require_super_admin)
):
    result = get_school_by_id(school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result


@router.put("/{school_id}")
def edit_school(
    school_id: int,
    school_data: schoolscreate,
    current_user: dict = Depends(require_super_admin)
):
    result = update_school(
        school_id, school_data.name, school_data.subdomain,
        school_data.admin_email, school_data.phone, school_data.address
    )
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result


@router.delete("/{school_id}")
def remove_school(
    school_id: int,
    current_user: dict = Depends(require_super_admin)
):
    result = delete_school(school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result