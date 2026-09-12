from database.db import get_db_connection, get_dict_cursor

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Total Students
    cursor.execute("SELECT COUNT(*) as count FROM students")
    students = cursor.fetchone()["count"]

    # Total Classes
    cursor.execute("SELECT COUNT(*) as count FROM classes")
    classes = cursor.fetchone()["count"]

    # Total Teachers
    cursor.execute("SELECT COUNT(*) as count FROM teachers")
    teachers = cursor.fetchone()["count"]

    # Today's Attendance
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE"
    )
    today_attendance = cursor.fetchone()["count"]

    # Today's Present
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND status = 'present'"
    )
    present_today = cursor.fetchone()["count"]

    # Today's Absent
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND status = 'absent'"
    )
    absent_today = cursor.fetchone()["count"]

    # Total Subjects
    cursor.execute("SELECT COUNT(*) as count FROM subjects")
    subjects = cursor.fetchone()["count"]

    conn.close()

    return {
        "students": students,
        "classes": classes,
        "teachers": teachers,
        "subjects": subjects,
        "today_attendance": today_attendance,
        "present_today": present_today,
        "absent_today": absent_today,
    }