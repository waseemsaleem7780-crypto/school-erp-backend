from database.db import get_db_connection, get_dict_cursor


def create_subject(name: str, class_id: int, teacher_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO subjects (name, class_id, teacher_id) VALUES (%s, %s, %s) RETURNING id",
        (name, class_id, teacher_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "class_id": class_id,
        "teacher_id": teacher_id
    }


def get_all_subjects():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, name, class_id, teacher_id FROM subjects ORDER BY class_id, name"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "class_id": row["class_id"],
            "teacher_id": row["teacher_id"]
        }
        for row in rows
    ]


def get_subjects_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, name, class_id, teacher_id FROM subjects WHERE class_id = %s ORDER BY name",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "class_id": row["class_id"],
            "teacher_id": row["teacher_id"]
        }
        for row in rows
    ]


def update_subject(subject_id: int, name: str, class_id: int, teacher_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE subjects SET name = %s, class_id = %s, teacher_id = %s WHERE id = %s RETURNING id",
        (name, class_id, teacher_id, subject_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {
        "id": subject_id,
        "name": name,
        "class_id": class_id,
        "teacher_id": teacher_id
    }


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