from database.db import get_db_connection, get_dict_cursor


def create_school(name: str, subdomain: str = None, admin_email: str = None, phone: str = None, address: str = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """INSERT INTO schools (name, subdomain, admin_email, phone, address) 
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (name, subdomain, admin_email, phone, address)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "subdomain": subdomain,
        "admin_email": admin_email,
        "phone": phone,
        "address": address
    }


def get_all_schools():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, subdomain, admin_email, phone, address, 
                  subscription_plan, subscription_expires_at, is_active, created_at 
           FROM schools 
           WHERE deleted_at IS NULL 
           ORDER BY id"""
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_school_by_id(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, subdomain, admin_email, phone, address, 
                  subscription_plan, subscription_expires_at, is_active, created_at 
           FROM schools 
           WHERE id = %s AND deleted_at IS NULL""",
        (school_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_school(school_id: int, name: str, subdomain: str = None, admin_email: str = None, phone: str = None, address: str = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE schools 
           SET name = %s, subdomain = %s, admin_email = %s, phone = %s, address = %s 
           WHERE id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (name, subdomain, admin_email, phone, address, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {
        "id": school_id,
        "name": name,
        "subdomain": subdomain,
        "admin_email": admin_email,
        "phone": phone,
        "address": address
    }


def delete_school(school_id: int):
    """Soft delete."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE schools 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (school_id,)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "School deleted (soft)", "id": school_id}


def get_school_stats():
    """Super admin ke liye overall stats."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT COUNT(*) as count FROM schools WHERE deleted_at IS NULL")
    total_schools = cursor.fetchone()["count"]

    cursor.execute(
        """SELECT COUNT(*) as count FROM users 
           WHERE role = 'admin' AND deleted_at IS NULL"""
    )
    total_admins = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM students WHERE deleted_at IS NULL")
    total_students = cursor.fetchone()["count"]

    conn.close()
    return {
        "total_schools": total_schools,
        "total_admins": total_admins,
        "total_students": total_students
    }