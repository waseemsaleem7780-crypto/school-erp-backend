from pydantic import BaseModel, validator
from typing import Optional
from services.auth_service import hash_password
from database.db import get_db_connection, get_dict_cursor


class SchoolEditWithPassword(BaseModel):
    name: str
    subdomain: Optional[str] = None
    admin_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    new_admin_password: Optional[str] = None  # ✅ Naya field


@router.put("/{school_id}")
def edit_school(
    school_id: int,
    school_data: SchoolEditWithPassword,
    current_user: dict = Depends(require_super_admin)
):
    """School edit + Admin password reset (Super Admin only)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. School update karo
        cursor.execute(
            """UPDATE schools 
               SET name = %s, subdomain = %s, admin_email = %s, phone = %s, address = %s 
               WHERE id = %s AND deleted_at IS NULL 
               RETURNING id""",
            (
                school_data.name,
                school_data.subdomain,
                school_data.admin_email,
                school_data.phone,
                school_data.address,
                school_id
            )
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="School not found")

        # 2. Agar naya password diya hai to admin ka password change karo
        new_password = school_data.new_admin_password
        if new_password and len(new_password) >= 8:
            # School ka admin user dhundo
            cursor.execute(
                """SELECT id FROM users 
                   WHERE school_id = %s AND role = 'admin' AND deleted_at IS NULL 
                   LIMIT 1""",
                (school_id,)
            )
            admin_user = cursor.fetchone()

            if admin_user:
                hashed = hash_password(new_password)
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed, admin_user["id"])
                )

        conn.commit()

        return {
            "id": school_id,
            "name": school_data.name,
            "subdomain": school_data.subdomain,
            "admin_email": school_data.admin_email,
            "phone": school_data.phone,
            "address": school_data.address,
            "password_updated": bool(new_password and len(new_password) >= 8),
            "message": "School updated successfully!" + 
                       (" Admin password bhi change ho gaya!" if new_password else "")
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()