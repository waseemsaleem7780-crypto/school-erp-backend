from database.db import get_db_connection, get_dict_cursor


def bulk_mark_attendance(records, marked_by, school_id):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    results = []

    try:
        for r in records:
            cursor.execute(
                """
                INSERT INTO attendance (student_id, date, status, marked_by, school_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (student_id, date)
                DO UPDATE SET status = EXCLUDED.status, marked_by = EXCLUDED.marked_by
                RETURNING id, student_id, date, status
                """,
                (r["student_id"], r["date"], r["status"], marked_by, school_id)
            )
            row = cursor.fetchone()
            results.append(dict(row))

        conn.commit()
        return {"message": "Attendance marked", "records": results}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_attendance_by_date_and_class(date, class_id, school_id, section_id=None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    query = """
        SELECT a.id, a.student_id, a.date, a.status,
               s.roll_number, u.name AS student_name
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        JOIN users u ON u.id = s.user_id
        WHERE a.date = %s AND s.class_id = %s AND a.school_id = %s
    """
    params = [date, class_id, school_id]

    if section_id:
        query += " AND s.section_id = %s"
        params.append(section_id)

    query += " ORDER BY s.roll_number"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_history(student_id, school_id, limit=30):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """
        SELECT id, student_id, date, status
        FROM attendance
        WHERE student_id = %s AND school_id = %s
        ORDER BY date DESC
        LIMIT %s
        """,
        (student_id, school_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_stats(date, school_id):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM attendance
        WHERE date = %s AND school_id = %s
        GROUP BY status
        """,
        (date, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["status"]: row["count"] for row in rows}