from database.db import get_db_connection, get_dict_cursor


def mark_attendance(student_id: int, date: str, status: str, class_id: int = None, section_id: int = None):
    """Ek student ki attendance mark karo (upsert)."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    # Pehle check karo ke is date pe already marked hai ya nahi
    cursor.execute(
        "SELECT id FROM attendance WHERE student_id = %s AND date = %s",
        (student_id, date)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update
        cursor.execute(
            "UPDATE attendance SET status = %s WHERE id = %s RETURNING id",
            (status, existing["id"])
        )
        record_id = cursor.fetchone()["id"]
    else:
        # Insert
        cursor.execute(
            """INSERT INTO attendance (student_id, date, status, class_id, section_id) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (student_id, date, status, class_id, section_id)
        )
        record_id = cursor.fetchone()["id"]
    
    conn.commit()
    conn.close()
    return {"id": record_id, "student_id": student_id, "date": date, "status": status}


def bulk_mark_attendance(attendance_list: list):
    """Multiple students ki attendance ek saath mark karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    results = []
    for item in attendance_list:
        student_id = item["student_id"]
        date = item["date"]
        status = item["status"]
        class_id = item.get("class_id")
        section_id = item.get("section_id")
        
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id = %s AND date = %s",
            (student_id, date)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE attendance SET status = %s WHERE id = %s RETURNING id",
                (status, existing["id"])
            )
        else:
            cursor.execute(
                """INSERT INTO attendance (student_id, date, status, class_id, section_id) 
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (student_id, date, status, class_id, section_id)
            )
        results.append(cursor.fetchone()["id"])
    
    conn.commit()
    conn.close()
    return {"message": f"{len(results)} attendance records saved", "count": len(results)}


def get_attendance_by_date_and_class(date: str, class_id: int, section_id: int = None):
    """Ek date aur class ke liye attendance dekho."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    if section_id:
        cursor.execute(
            """SELECT a.id, a.student_id, a.date, a.status, a.class_id, a.section_id
               FROM attendance a
               WHERE a.date = %s AND a.class_id = %s AND a.section_id = %s
               ORDER BY a.student_id""",
            (date, class_id, section_id)
        )
    else:
        cursor.execute(
            """SELECT a.id, a.student_id, a.date, a.status, a.class_id, a.section_id
               FROM attendance a
               WHERE a.date = %s AND a.class_id = %s
               ORDER BY a.student_id""",
            (date, class_id)
        )
    
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "student_id": r["student_id"],
            "date": str(r["date"]),
            "status": r["status"],
            "class_id": r["class_id"],
            "section_id": r["section_id"],
        }
        for r in rows
    ]


def get_attendance_history(student_id: int, limit: int = 30):
    """Ek student ki attendance history."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, student_id, date, status 
           FROM attendance 
           WHERE student_id = %s 
           ORDER BY date DESC 
           LIMIT %s""",
        (student_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "student_id": r["student_id"],
            "date": str(r["date"]),
            "status": r["status"],
        }
        for r in rows
    ]


def get_attendance_stats(date: str):
    """Ek date ki overall attendance stats."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
            SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent
           FROM attendance 
           WHERE date = %s""",
        (date,)
    )
    row = cursor.fetchone()
    conn.close()
    
    total = row["total"] or 0
    present = row["present"] or 0
    absent = row["absent"] or 0
    percentage = round((present / total * 100), 2) if total > 0 else 0
    
    return {
        "date": date,
        "total": total,
        "present": present,
        "absent": absent,
        "percentage": percentage
    }