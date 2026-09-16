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
    return {"id": new_id, "name": name, "code": code, "class_id": class_id}


def get_all_subjects():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, name, code, class_id FROM subjects ORDER BY class_id, name")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r["id"], "name": r["name"], "code": r["code"], "class_id": r["class_id"]}
        for r in rows
    ]


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
        {"id": r["id"], "name": r["name"], "code": r["code"], "class_id": r["class_id"]}
        for r in rows
    ]


def update_subject(subject_id: int, name: str, code: str, class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE subjects SET name = %s, code = %s, class_id = %s WHERE id = %s RETURNING id",
        (name, code, class_id, subject_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"id": subject_id, "name": name, "code": code, "class_id": class_id}


def delete_subject(subject_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("DELETE FROM subjects WHERE id = %s RETURNING id", (subject_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Subject deleted", "id": subject_id}