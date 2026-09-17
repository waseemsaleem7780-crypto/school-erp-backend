from database.db import get_db_connection, get_dict_cursor


def create_class(name: str, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO classes (name, school_id) VALUES (%s, %s) RETURNING id",
        (name, school_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "school_id": school_id
    }


def get_all_classes(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name FROM classes 
           WHERE school_id = %s AND deleted_at IS NULL 
           ORDER BY name""",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "name": row["name"]}
        for row in rows
    ]


def update_class(class_id: int, name: str, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE classes 
           SET name = %s 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (name, class_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {"id": class_id, "name": name, "school_id": school_id}


def delete_class(class_id: int, school_id: int):
    """Soft delete."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE classes 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (class_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {"message": "Class deleted (soft)", "id": class_id}


def restore_class(class_id: int, school_id: int):
    """Restore soft-deleted class."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE classes 
           SET deleted_at = NULL 
           WHERE id = %s AND school_id = %s AND deleted_at IS NOT NULL 
           RETURNING id""",
        (class_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {"message": "Class restored", "id": class_id}