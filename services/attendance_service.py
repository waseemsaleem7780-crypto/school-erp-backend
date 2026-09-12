from database.db import get_db_connection, get_dict_cursor

def create_attendance(student_id: int, date: str, status: str, marked_by: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO attendance (student_id, date, status, marked_by) VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (student_id, date) DO UPDATE SET status = EXCLUDED.status",
        (student_id, date, status, marked_by)
    )
    conn.commit()
    conn.close()
    return {
        "message": "Attendance marked successfully",
        "student_id": student_id,
        "date": date,
        "status": status
    }

def get_attendance_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, student_id, date, status, marked_by, marked_at FROM attendance WHERE student_id = %s ORDER BY date DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "date": row["date"],
            "status": row["status"],
            "marked_by": row["marked_by"],
            "marked_at": row["marked_at"]
        }
        for row in rows
    ]