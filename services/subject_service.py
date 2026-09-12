from database.db import get_db_connection, get_dict_cursor

def create_subject(name: str, code: str, class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO subjects (name, code, class_id) VALUES (%s, %s, %s) RETURNING id",
        (name, code, class_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "code": code,
        "class_id": class_id
    }

def get_subjects_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, name, code, class_id FROM subjects WHERE class_id = %s ORDER BY name",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "code": row["code"],
            "class_id": row["class_id"]
        }
        for row in rows
    ]