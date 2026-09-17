from database.db import get_db_connection, get_dict_cursor


def create_student(user_id: int, roll_number: str, class_id: int, section_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """INSERT INTO students (user_id, roll_number, class_id, section_id, school_id) 
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (user_id, roll_number, class_id, section_id, school_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "user_id": user_id,
        "roll_number": roll_number,
        "class_id": class_id,
        "section_id": section_id,
        "school_id": school_id
    }


def get_students_by_class(class_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, roll_number, class_id, section_id, school_id 
           FROM students 
           WHERE class_id = %s AND school_id = %s AND deleted_at IS NULL 
           ORDER BY roll_number""",
        (class_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_students(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, roll_number, class_id, section_id, school_id 
           FROM students 
           WHERE school_id = %s AND deleted_at IS NULL 
           ORDER BY id""",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_student(student_id: int, roll_number: str, class_id: int, section_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE students 
           SET roll_number = %s, class_id = %s, section_id = %s 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (roll_number, class_id, section_id, student_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {
        "id": student_id,
        "roll_number": roll_number,
        "class_id": class_id,
        "section_id": section_id,
        "school_id": school_id
    }


def delete_student(student_id: int, school_id: int):
    """Soft delete — data safe rehta hai."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE students 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (student_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Student deleted (soft)", "id": student_id}


def restore_student(student_id: int, school_id: int):
    """Soft-deleted student ko restore karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE students 
           SET deleted_at = NULL 
           WHERE id = %s AND school_id = %s AND deleted_at IS NOT NULL 
           RETURNING id""",
        (student_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Student restored", "id": student_id}


def get_deleted_students(school_id: int):
    """Soft-deleted students ki list."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, user_id, roll_number, class_id, section_id, deleted_at 
           FROM students 
           WHERE school_id = %s AND deleted_at IS NOT NULL 
           ORDER BY deleted_at DESC""",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]