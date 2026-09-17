from database.db import get_db_connection, get_dict_cursor


def get_dashboard_stats(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Total Students
    cursor.execute(
        "SELECT COUNT(*) as count FROM students WHERE school_id = %s AND deleted_at IS NULL",
        (school_id,)
    )
    students = cursor.fetchone()["count"]

    # Total Classes
    cursor.execute(
        "SELECT COUNT(*) as count FROM classes WHERE school_id = %s AND deleted_at IS NULL",
        (school_id,)
    )
    classes = cursor.fetchone()["count"]

    # Total Teachers
    cursor.execute(
        "SELECT COUNT(*) as count FROM teachers WHERE school_id = %s AND deleted_at IS NULL",
        (school_id,)
    )
    teachers = cursor.fetchone()["count"]

    # Total Subjects
    cursor.execute(
        "SELECT COUNT(*) as count FROM subjects WHERE school_id = %s AND deleted_at IS NULL",
        (school_id,)
    )
    subjects = cursor.fetchone()["count"]

    # Today's Attendance Total
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND school_id = %s",
        (school_id,)
    )
    today_attendance = cursor.fetchone()["count"]

    # Today's Present
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND status = 'present' AND school_id = %s",
        (school_id,)
    )
    present_today = cursor.fetchone()["count"]

    # Today's Half Day
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND status = 'half_day' AND school_id = %s",
        (school_id,)
    )
    half_day_today = cursor.fetchone()["count"]

    # Today's Not Present
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE date = CURRENT_DATE AND status != 'present' AND school_id = %s",
        (school_id,)
    )
    not_present_today = cursor.fetchone()["count"]

    conn.close()

    return {
        "students": students,
        "classes": classes,
        "teachers": teachers,
        "subjects": subjects,
        "today_attendance": today_attendance,
        "present_today": present_today,
        "half_day_today": half_day_today,
        "absent_today": not_present_today,
    }