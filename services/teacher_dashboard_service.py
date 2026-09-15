from database.db import get_db_connection, get_dict_cursor

def get_teacher_stats(user_id: int):
    """Teacher ke dashboard ke stats"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Total classes
    cursor.execute("SELECT COUNT(*) as count FROM classes")
    total_classes = cursor.fetchone()["count"]

    # Total students
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()["count"]

    # Total homework (jo is teacher ne di)
    cursor.execute(
        "SELECT COUNT(*) as count FROM homework WHERE teacher_id = (SELECT id FROM teachers WHERE user_id = %s)",
        (user_id,)
    )
    total_homework = cursor.fetchone()["count"]

    # Total attendance marked (aaj)
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE"
    )
    today_attendance = cursor.fetchone()["count"]

    conn.close()

    return {
        "total_classes": total_classes,
        "total_students": total_students,
        "total_homework": total_homework,
        "today_attendance": today_attendance,
    }


def get_teacher_classes(user_id: int):
    """Teacher ki assigned classes (abhi saari classes return karo)"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id, name FROM classes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
        }
        for row in rows
    ]


def get_teacher_students(class_id: int):
    """Class ke students"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        "SELECT id, user_id, roll_number, class_id, section_id FROM students WHERE class_id = %s ORDER BY roll_number",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "roll_number": row["roll_number"],
            "class_id": row["class_id"],
            "section_id": row["section_id"],
        }
        for row in rows
    ]