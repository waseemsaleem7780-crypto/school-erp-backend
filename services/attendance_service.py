from database.db import get_db_connection, get_dict_cursor


def bulk_mark_attendance(attendance_list: list, marked_by: int, school_id: int):
    """Multiple students ki attendance ek saath mark karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    results = []
    for item in attendance_list:
        student_id = item["student_id"]
        date = item["date"]
        status = item["status"]

        # Pehle check karo ke already marked hai ya nahi
        cursor.execute(
            """SELECT id FROM attendance 
               WHERE student_id = %s AND date = %s AND school_id = %s""",
            (student_id, date, school_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """UPDATE attendance 
                   SET status = %s, marked_by = %s 
                   WHERE id = %s 
                   RETURNING id""",
                (status, marked_by, existing["id"])
            )
        else:
            cursor.execute(
                """INSERT INTO attendance (student_id, date, status, marked_by, school_id) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (student_id, date, status, marked_by, school_id)
            )
        results.append(cursor.fetchone()["id"])

    conn.commit()
    conn.close()
    return {"message": f"{len(results)} attendance records saved", "count": len(results)}


def get_attendance_by_date_and_class(date: str, class_id: int, school_id: int, section_id: int = None):
    """Ek date aur class ke liye attendance dekho (students table se join)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    if section_id:
        cursor.execute(
            """SELECT a.id, a.student_id, a.date, a.status, a.marked_by
               FROM attendance a
               JOIN students s ON s.id = a.student_id
               WHERE a.date = %s AND s.class_id = %s AND s.section_id = %s 
                     AND a.school_id = %s AND s.deleted_at IS NULL
               ORDER BY s.roll_number""",
            (date, class_id, section_id, school_id)
        )
    else:
        cursor.execute(
            """SELECT a.id, a.student_id, a.date, a.status, a.marked_by
               FROM attendance a
               JOIN students s ON s.id = a.student_id
               WHERE a.date = %s AND s.class_id = %s AND a.school_id = %s 
                     AND s.deleted_at IS NULL
               ORDER BY s.roll_number""",
            (date, class_id, school_id)
        )

    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "student_id": r["student_id"],
            "date": str(r["date"]),
            "status": r["status"],
            "marked_by": r["marked_by"],
        }
        for r in rows
    ]


def get_attendance_stats(date: str, school_id: int):
    """Ek date ki overall attendance stats."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
            SUM(CASE WHEN status = 'half_day' THEN 1 ELSE 0 END) as half_day,
            SUM(CASE WHEN status NOT IN ('present', 'half_day') THEN 1 ELSE 0 END) as absent
           FROM attendance 
           WHERE date = %s AND school_id = %s""",
        (date, school_id)
    )
    row = cursor.fetchone()
    conn.close()

    total = row["total"] or 0
    present = row["present"] or 0
    half_day = row["half_day"] or 0
    absent = row["absent"] or 0
    percentage = round((present / total * 100), 2) if total > 0 else 0

    return {
        "date": date,
        "total": total,
        "present": present,
        "half_day": half_day,
        "absent": absent,
        "percentage": percentage
    }


def get_attendance_history(student_id: int, school_id: int, limit: int = 30):
    """Ek student ki attendance history."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, student_id, date, status, marked_by
           FROM attendance 
           WHERE student_id = %s AND school_id = %s 
           ORDER BY date DESC 
           LIMIT %s""",
        (student_id, school_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]