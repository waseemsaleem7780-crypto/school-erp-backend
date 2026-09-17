from database.db import get_db_connection, get_dict_cursor


def create_section(name: str, class_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO sections (name, class_id, school_id) VALUES (%s, %s, %s) RETURNING id",
        (name, class_id, school_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "class_id": class_id,
        "school_id": school_id
    }


def get_sections_by_class(class_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, class_id FROM sections 
           WHERE class_id = %s AND school_id = %s AND deleted_at IS NULL 
           ORDER BY name""",
        (class_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "name": row["name"], "class_id": row["class_id"]}
        for row in rows
    ]


def get_all_sections(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, name, class_id FROM sections 
           WHERE school_id = %s AND deleted_at IS NULL 
           ORDER BY id""",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": row["id"], "name": row["name"], "class_id": row["class_id"]}
        for row in rows
    ]


def update_section(section_id: int, name: str, class_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE sections 
           SET name = %s, class_id = %s 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (name, class_id, section_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {
        "id": section_id,
        "name": name,
        "class_id": class_id,
        "school_id": school_id
    }


def delete_section(section_id: int, school_id: int):
    """Soft delete — data safe rehta hai."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE sections 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (section_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {"message": "Section deleted (soft)", "id": section_id}


def restore_section(section_id: int, school_id: int):
    """Soft-deleted section ko restore karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE sections 
           SET deleted_at = NULL 
           WHERE id = %s AND school_id = %s AND deleted_at IS NOT NULL 
           RETURNING id""",
        (section_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        return None

    return {"message": "Section restored", "id": section_id}