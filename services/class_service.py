from database.db import get_db_connection, get_dict_cursor


def create_class(name: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO classes (name) VALUES (%s) RETURNING id",
        (name,)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {"id": new_id, "name": name}


def get_all_classes():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, name FROM classes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "name": row["name"]} for row in rows]


def update_class(class_id: int, name: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE classes SET name = %s WHERE id = %s RETURNING id",
        (name, class_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"id": class_id, "name": name}


def delete_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("DELETE FROM classes WHERE id = %s RETURNING id", (class_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"message": "Class deleted", "id": class_id}