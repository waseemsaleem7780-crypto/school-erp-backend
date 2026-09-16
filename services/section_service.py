from database.db import get_db_connection, get_dict_cursor


def create_section(name: str, class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO sections (name, class_id) VALUES (%s, %s) RETURNING id",
        (name, class_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "class_id": class_id
    }


def get_sections_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, name, class_id FROM sections WHERE class_id = %s ORDER BY name",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "name": row["name"], "class_id": row["class_id"]}
        for row in rows
    ]


def get_all_sections():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, name, class_id FROM sections ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "name": row["name"], "class_id": row["class_id"]}
        for row in rows
    ]


def update_section(section_id: int, name: str, class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE sections SET name = %s, class_id = %s WHERE id = %s RETURNING id",
        (name, class_id, section_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"id": section_id, "name": name, "class_id": class_id}


def delete_section(section_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("DELETE FROM sections WHERE id = %s RETURNING id", (section_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"message": "Section deleted", "id": section_id}