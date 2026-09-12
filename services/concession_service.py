from database.db import get_db_connection, get_dict_cursor

def create_concession(student_id: int, user_id: int, academic_year_id: int, concession_type: str, concession_value: float, reason: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO concession (student_id, user_id, academic_year_id, concession_type, concession_value, reason) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (student_id, user_id, academic_year_id, concession_type, concession_value, reason)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "student_id": student_id,
        "user_id": user_id,
        "academic_year_id": academic_year_id,
        "concession_type": concession_type,
        "concession_value": concession_value,
        "reason": reason
    }

def get_concessions_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, student_id, user_id, academic_year_id, concession_type, concession_value, reason, granted_at FROM concession WHERE student_id = %s ORDER BY granted_at DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "user_id": row["user_id"],
            "academic_year_id": row["academic_year_id"],
            "concession_type": row["concession_type"],
            "concession_value": row["concession_value"],
            "reason": row["reason"],
            "granted_at": row["granted_at"]
        }
        for row in rows
    ]