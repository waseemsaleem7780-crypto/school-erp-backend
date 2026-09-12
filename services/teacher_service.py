from database.db import get_db_connection, get_dict_cursor

def create_teacher(user_id: int, qualification: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO teachers (user_id, qualification) VALUES (%s, %s) RETURNING id",
        (user_id, qualification)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "user_id": user_id,
        "qualification": qualification
    }

def get_all_teachers():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, user_id, qualification, hired_date FROM teachers ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "qualification": row["qualification"],
            "hired_date": row["hired_date"]
        }
        for row in rows
    ]