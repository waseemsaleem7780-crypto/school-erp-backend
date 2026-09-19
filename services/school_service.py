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
    """
    School delete karo + us school ke SAARE users bhi soft-delete karo.
    - School
    - Admins
    - Teachers
    - Students
    - Parents (guardians)
    """
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. Pehle check karo school exist karta hai
        cursor.execute(
            "SELECT id FROM schools WHERE id = %s AND deleted_at IS NULL",
            (school_id,)
        )
        if not cursor.fetchone():
            conn.close()
            return None

        # 2. School ke saare users soft-delete karo
        cursor.execute(
            """UPDATE users 
               SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        users_deleted = cursor.rowcount

        # 3. School ke saare students soft-delete karo
        cursor.execute(
            """UPDATE students 
               SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        students_deleted = cursor.rowcount

        # 4. School ke saare teachers soft-delete karo
        cursor.execute(
            """UPDATE teachers 
               SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        teachers_deleted = cursor.rowcount

        # 5. School khud soft-delete karo
        cursor.execute(
            """UPDATE schools 
               SET deleted_at = CURRENT_TIMESTAMP 
               WHERE id = %s AND deleted_at IS NULL""",
            (school_id,)
        )

        conn.commit()
        conn.close()

        return {
            "message": "School deleted (soft) + all users",
            "id": school_id,
            "users_deleted": users_deleted,
            "students_deleted": students_deleted,
            "teachers_deleted": teachers_deleted
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


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