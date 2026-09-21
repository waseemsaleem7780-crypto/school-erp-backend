from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
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


# ============ SCHEMA ============
class SchoolWithAdminCreate(BaseModel):
    name: str
    subdomain: str
    admin_name: str
    admin_email: str
    admin_password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: Optional[str] = "trial"
    institute_type: Optional[str] = "school"
    whatsapp_provider: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_account_sid: Optional[str] = None
    whatsapp_auth_token: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None


class InstituteTypeUpdate(BaseModel):
    """Super admin school ka mode change kare."""
    institute_type: str


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
        cursor.execute(
            "SELECT id FROM schools WHERE subdomain = %s",
            (data.subdomain,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Subdomain already exists")

        # 2. Check email unique
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (data.admin_email,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 3. School banao
        cursor.execute(
            """INSERT INTO schools 
               (name, subdomain, admin_email, phone, address, subscription_plan, institute_type,
                whatsapp_provider, whatsapp_number, whatsapp_account_sid,
                whatsapp_auth_token, whatsapp_api_key, whatsapp_phone_id) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                data.name, data.subdomain, data.admin_email, data.phone,
                data.address, data.subscription_plan, data.institute_type or 'school',
                data.whatsapp_provider, data.whatsapp_number,
                data.whatsapp_account_sid, data.whatsapp_auth_token,
                data.whatsapp_api_key, data.whatsapp_phone_id
            )
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

        base_url = "https://school-erp-frontend-azure.vercel.app"
        login_url = f"{base_url}/{data.subdomain}/login"

        return {
            "school_id": school_id,
            "user_id": user_id,
            "name": data.name,
            "subdomain": data.subdomain,
            "institute_type": data.institute_type or 'school',
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


# ============ GET SCHOOL BY SUBDOMAIN ============
@router.get("/by-subdomain/{subdomain}")
def get_school_by_subdomain(subdomain: str):
    """Subdomain se school dhundo (login page ke liye)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, subdomain, is_active,
                  COALESCE(institute_type, 'school') as institute_type
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


# ============ CURRENT SCHOOL SETTINGS (ADMIN — READ ONLY) ============
@router.get("/settings")
def get_school_settings(
    current_user: dict = Depends(get_current_user)
):
    """Current school ki settings lo — admin sirf read kar sakta hai."""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(400, "No school assigned")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        """SELECT id, name, subdomain, phone, address,
                  COALESCE(institute_type, 'school') as institute_type,
                  subscription_plan
           FROM schools 
           WHERE id = %s AND deleted_at IS NULL""",
        (school_id,)
    )
    school = cursor.fetchone()
    conn.close()

    if not school:
        raise HTTPException(404, "School not found")

    return dict(school)


# ❌ REMOVED: PUT /settings — admin mode change nahi kar sakta


# ============ SUPER ADMIN: CHANGE INSTITUTE TYPE ============
@router.put("/{school_id}/institute-type")
def update_institute_type(
    school_id: int,
    data: InstituteTypeUpdate,
    current_user: dict = Depends(require_super_admin)
):
    """Sirf super admin school ka mode change kar sakta hai."""
    if data.institute_type not in ["school", "academy", "college", "madrassa"]:
        raise HTTPException(400, "Invalid institute_type. Use: school, academy, college, madrassa")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute(
            """UPDATE schools 
               SET institute_type = %s 
               WHERE id = %s AND deleted_at IS NULL
               RETURNING id, name, institute_type""",
            (data.institute_type, school_id)
        )
        result = cursor.fetchone()
        conn.commit()

        if not result:
            raise HTTPException(404, "School not found")

        return {
            "success": True,
            "message": f"Mode updated to {result['institute_type']}",
            "school_id": result["id"],
            "school_name": result["name"],
            "institute_type": result["institute_type"],
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        conn.close()


# ============ GET ALL SCHOOLS ============
@router.get("/")
def get_schools(current_user: dict = Depends(require_super_admin)):
    """Sirf super admin saare schools dekh sakta hai."""
    return get_all_schools()


# ============ STATS ============
@router.get("/stats")
def school_stats(current_user: dict = Depends(require_super_admin)):
    """Overall stats — total schools, admins, students."""
    return get_school_stats()


# ============ ADMIN ACTIVITY ============
@router.get("/admin-activity")
def admin_activity(current_user: dict = Depends(require_super_admin)):
    """Kaunse admins active hain, kaunse nahi."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("""
        SELECT 
            u.id,
            u.full_name,
            u.email,
            u.school_id,
            s.name as school_name,
            u.last_login,
            u.login_count,
            u.is_active,
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
            "id": r["id"],
            "full_name": r["full_name"],
            "email": r["email"],
            "school_id": r["school_id"],
            "school_name": r["school_name"],
            "last_login": str(r["last_login"]) if r["last_login"] else None,
            "login_count": r["login_count"] or 0,
            "is_active": r["is_active"],
            "status": r["status"],
        }
        for r in rows
    ]


# ============ DYNAMIC ROUTES (ALWAYS LAST) ============
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
    """School edit karo — WhatsApp config bhi."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute(
            """UPDATE schools 
               SET name = %s, subdomain = %s, admin_email = %s, phone = %s, address = %s,
                   whatsapp_provider = COALESCE(%s, whatsapp_provider),
                   whatsapp_number = COALESCE(%s, whatsapp_number),
                   whatsapp_account_sid = COALESCE(%s, whatsapp_account_sid),
                   whatsapp_auth_token = COALESCE(%s, whatsapp_auth_token),
                   whatsapp_api_key = COALESCE(%s, whatsapp_api_key),
                   whatsapp_phone_id = COALESCE(%s, whatsapp_phone_id)
               WHERE id = %s AND deleted_at IS NULL RETURNING id""",
            (
                school_data.name, school_data.subdomain, school_data.admin_email,
                school_data.phone, school_data.address,
                school_data.whatsapp_provider, school_data.whatsapp_number,
                school_data.whatsapp_account_sid, school_data.whatsapp_auth_token,
                school_data.whatsapp_api_key, school_data.whatsapp_phone_id,
                school_id
            )
        )
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="School not found")
        
        return {"id": school_id, "message": "School updated!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/{school_id}")
def remove_school(
    school_id: int,
    current_user: dict = Depends(require_super_admin)
):
    result = delete_school(school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result