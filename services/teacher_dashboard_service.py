from database.db import get_db_connection, get_dict_cursor


def get_teacher_stats(user_id: int):
    """Teacher ke dashboard stats"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    result = {
        "classes_count": 0,
        "students_count": 0,
        "subjects_count": 0,
        "attendance_marked_today": 0,
    }
    try:
        # Teacher ka id nikaalo
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
        teacher = cursor.fetchone()
        if not teacher:
            print(f"No teacher record found for user_id={user_id}")
            return result

        teacher_id = teacher["id"]

        # Subjects count
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM subjects WHERE teacher_id = %s",
                (teacher_id,)
            )
            result["subjects_count"] = cursor.fetchone()["c"]
        except Exception as e:
            print("subjects error:", e)

        # Classes count (unique class_ids from subjects)
        try:
            cursor.execute(
                "SELECT COUNT(DISTINCT class_id) as c FROM subjects WHERE teacher_id = %s",
                (teacher_id,)
            )
            result["classes_count"] = cursor.fetchone()["c"]
        except Exception as e:
            print("classes error:", e)

        # Students count (all students in teacher's classes)
        try:
            cursor.execute(
                """SELECT COUNT(DISTINCT s.id) as c 
                   FROM students s
                   WHERE s.class_id IN (
                       SELECT DISTINCT class_id FROM subjects WHERE teacher_id = %s
                   )""",
                (teacher_id,)
            )
            result["students_count"] = cursor.fetchone()["c"]
        except Exception as e:
            print("students error:", e)

        # Today's attendance marked
        try:
            cursor.execute(
                """SELECT COUNT(*) as c FROM attendance 
                   WHERE marked_by = %s AND date = CURRENT_DATE""",
                (teacher_id,)
            )
            result["attendance_marked_today"] = cursor.fetchone()["c"]
        except Exception as e:
            print("attendance today error:", e)

        return result
    except Exception as e:
        print("teacher stats error:", e)
        return result
    finally:
        conn.close()


def get_teacher_classes(user_id: int):
    """Teacher ki classes aur subjects"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
        teacher = cursor.fetchone()
        if not teacher:
            return []

        teacher_id = teacher["id"]

        cursor.execute(
            """SELECT 
                s.id as subject_id,
                s.name as subject_name,
                s.code as subject_code,
                s.class_id,
                c.name as class_name
               FROM subjects s
               LEFT JOIN classes c ON c.id = s.class_id
               WHERE s.teacher_id = %s
               ORDER BY s.class_id, s.name""",
            (teacher_id,)
        )
        rows = cursor.fetchall()
        return [
            {
                "subject_id": r["subject_id"],
                "subject_name": r["subject_name"],
                "subject_code": r["subject_code"],
                "class_id": r["class_id"],
                "class_name": r["class_name"] or f"Class #{r['class_id']}",
            }
            for r in rows
        ]
    except Exception as e:
        print("teacher classes error:", e)
        return []
    finally:
        conn.close()


def get_teacher_students(class_id: int):
    """Class ke students"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute(
            """SELECT 
                s.id, s.user_id, s.roll_number, s.class_id, s.section_id,
                u.full_name as student_name,
                u.email as student_email
               FROM students s
               LEFT JOIN users u ON u.id = s.user_id
               WHERE s.class_id = %s
               ORDER BY s.roll_number""",
            (class_id,)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "roll_number": r["roll_number"],
                "class_id": r["class_id"],
                "section_id": r["section_id"],
                "student_name": r["student_name"],
                "student_email": r["student_email"],
            }
            for r in rows
        ]
    except Exception as e:
        print("teacher students error:", e)
        return []
    finally:
        conn.close()