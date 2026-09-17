from database.db import get_db_connection, get_dict_cursor


def create_teacher(user_id: int, qualification: str, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """INSERT INTO teachers (user_id, qualification, school_id) 
           VALUES (%s, %s, %s) RETURNING id""",
        (user_id, qualification, school_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "user_id": user_id,
        "qualification": qualification,
        "school_id": school_id
    }


def get_all_teachers(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, qualification, hired_date 
           FROM teachers 
           WHERE school_id = %s AND deleted_at IS NULL 
           ORDER BY id""",
        (school_id,)
    )
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


def update_teacher(teacher_id: int, qualification: str, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE teachers 
           SET qualification = %s 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (qualification, teacher_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {
        "id": teacher_id,
        "qualification": qualification,
        "school_id": school_id
    }


def delete_teacher(teacher_id: int, school_id: int):
    """Soft delete."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE teachers 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (teacher_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Teacher deleted (soft)", "id": teacher_id}


def restore_teacher(teacher_id: int, school_id: int):
    """Restore soft-deleted teacher."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE teachers 
           SET deleted_at = NULL 
           WHERE id = %s AND school_id = %s AND deleted_at IS NOT NULL 
           RETURNING id""",
        (teacher_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Teacher restored", "id": teacher_id}