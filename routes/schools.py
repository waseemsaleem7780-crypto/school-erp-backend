from fastapi import APIRouter, Depends, HTTPException
from models.schemas import schoolscreate
from services.school_service import (
    create_school,
    get_all_schools,
    get_school_by_id,
    update_school,
    delete_school,
    get_school_stats,
)
from utils.dependencies import get_current_user, require_super_admin

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post("/", status_code=201)
def add_school(
    school_data: schoolscreate,
    current_user: dict = Depends(require_super_admin)
):
    """Sirf super admin naya school add kar sakta hai."""
    return create_school(
        school_data.name,
        school_data.subdomain,
        school_data.admin_email,
        school_data.phone,
        school_data.address
    )


@router.get("/")
def get_schools(current_user: dict = Depends(require_super_admin)):
    """Sirf super admin saare schools dekh sakta hai."""
    return get_all_schools()


@router.get("/stats")
def school_stats(current_user: dict = Depends(require_super_admin)):
    """Overall stats — total schools, admins, students."""
    return get_school_stats()


# ✅ Admin activity endpoint — super admin ke liye
@router.get("/admin-activity")
def admin_activity(current_user: dict = Depends(require_super_admin)):
    """Kaunse admins active hain, kaunse nahi."""
    from database.db import get_db_connection, get_dict_cursor

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


# ⚠️ Dynamic routes ALWAYS last mein rakho
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
        school_id,
        school_data.name,
        school_data.subdomain,
        school_data.admin_email,
        school_data.phone,
        school_data.address
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