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
        "id": new_id, "name": name, "subdomain": subdomain,
        "admin_email": admin_email, "phone": phone, "address": address
    }


def get_all_schools():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, subdomain, admin_email, phone, address, 
                  subscription_plan, subscription_expires_at, is_active, created_at 
           FROM schools WHERE deleted_at IS NULL ORDER BY id"""
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
           FROM schools WHERE id = %s AND deleted_at IS NULL""",
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
           WHERE id = %s AND deleted_at IS NULL RETURNING id""",
        (name, subdomain, admin_email, phone, address, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {
        "id": school_id, "name": name, "subdomain": subdomain,
        "admin_email": admin_email, "phone": phone, "address": address
    }


def delete_school(school_id: int):
    """
    School delete karo + us school ka SAARA data soft-delete karo:
    - School
    - Users (admin, teacher, student, parent)
    - Students
    - Teachers
    - Guardians
    - Classes
    - Sections
    - Subjects
    - Attendance
    - Fees
    - Homework
    - Exams
    - Results
    - Assignments
    - Notice Board
    - Study Material
    - Timetable
    - Concessions
    """
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. Check school exist karta hai
        cursor.execute(
            "SELECT id FROM schools WHERE id = %s AND deleted_at IS NULL",
            (school_id,)
        )
        if not cursor.fetchone():
            conn.close()
            return None

        deleted = {}

        # 2. Users (admin, teacher, student, parent)
        cursor.execute(
            """UPDATE users SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["users"] = cursor.rowcount

        # 3. Students
        cursor.execute(
            """UPDATE students SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["students"] = cursor.rowcount

        # 4. Teachers
        cursor.execute(
            """UPDATE teachers SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["teachers"] = cursor.rowcount

        # 5. Guardians (student ke through)
        cursor.execute(
            """UPDATE guardians SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["guardians"] = cursor.rowcount

        # 6. Classes
        cursor.execute(
            """UPDATE classes SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["classes"] = cursor.rowcount

        # 7. Sections (class ke through)
        cursor.execute(
            """UPDATE sections SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["sections"] = cursor.rowcount

        # 8. Subjects (class ke through)
        cursor.execute(
            """UPDATE subjects SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["subjects"] = cursor.rowcount

        # 9. Attendance
        cursor.execute(
            """UPDATE attendance SET deleted_at = CURRENT_TIMESTAMP 
               WHERE school_id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["attendance"] = cursor.rowcount

        # 10. Fees (payment + structure)
        cursor.execute(
            """UPDATE fee_payment SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["fee_payments"] = cursor.rowcount

        # 11. Homework (student ke through)
        cursor.execute(
            """UPDATE homework SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["homework"] = cursor.rowcount

        # 12. Exams (class ke through)
        cursor.execute(
            """UPDATE exam SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["exams"] = cursor.rowcount

        # 13. Results (student ke through)
        cursor.execute(
            """UPDATE results SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["results"] = cursor.rowcount

        # 14. Assignments (student ke through)
        cursor.execute(
            """UPDATE assignment SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["assignments"] = cursor.rowcount

        # 15. Notice Board
        cursor.execute(
            """UPDATE notice_board SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["notice_board"] = cursor.rowcount

        # 16. Study Material
        cursor.execute(
            """UPDATE study_material SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["study_material"] = cursor.rowcount

        # 17. Timetable
        cursor.execute(
            """UPDATE timetable SET deleted_at = CURRENT_TIMESTAMP 
               WHERE class_id IN (
                   SELECT id FROM classes WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["timetable"] = cursor.rowcount

        # 18. Concessions
        cursor.execute(
            """UPDATE concession SET deleted_at = CURRENT_TIMESTAMP 
               WHERE student_id IN (
                   SELECT id FROM students WHERE school_id = %s
               ) AND deleted_at IS NULL""",
            (school_id,)
        )
        deleted["concessions"] = cursor.rowcount

        # 19. School khud
        cursor.execute(
            """UPDATE schools SET deleted_at = CURRENT_TIMESTAMP 
               WHERE id = %s AND deleted_at IS NULL""",
            (school_id,)
        )

        conn.commit()
        conn.close()

        return {
            "message": "School + ALL data deleted",
            "school_id": school_id,
            "deleted_counts": deleted
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


def get_school_stats():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT COUNT(*) as count FROM schools WHERE deleted_at IS NULL")
    total_schools = cursor.fetchone()["count"]
    cursor.execute(
        "SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND deleted_at IS NULL"
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