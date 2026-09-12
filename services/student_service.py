from database.db import get_db_connection, get_dict_cursor

def create_student(user_id: int, roll_number: str, class_id: int, section_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO students (user_id, roll_number, class_id, section_id) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, roll_number, class_id, section_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "user_id": user_id,
        "roll_number": roll_number,
        "class_id": class_id,
        "section_id": section_id
    }

def get_students_by_class(class_id: int):
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
            "section_id": row["section_id"]
        }
        for row in rows
    ]