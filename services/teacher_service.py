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
            "hired_date": str(row["hired_date"])
        }
        for row in rows
    ]


def update_teacher(teacher_id: int, qualification: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE teachers SET qualification = %s WHERE id = %s RETURNING id",
        (qualification, teacher_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {
        "id": teacher_id,
        "qualification": qualification
    }


def delete_teacher(teacher_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("DELETE FROM teachers WHERE id = %s RETURNING id", (teacher_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"message": "Teacher deleted", "id": teacher_id}