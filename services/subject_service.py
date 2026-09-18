from database.db import get_db_connection, get_dict_cursor


def create_subject(name: str, code: str, class_id: int, teacher_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """INSERT INTO subjects (name, code, class_id, teacher_id, school_id) 
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (name, code, class_id, teacher_id, school_id)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "code": code,
        "class_id": class_id,
        "teacher_id": teacher_id,
        "school_id": school_id
    }


def get_all_subjects(school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
            s.id, s.name, s.code, s.class_id, s.teacher_id,
            t.qualification as teacher_qualification,
            u.full_name as teacher_name
           FROM subjects s
           LEFT JOIN teachers t ON t.id = s.teacher_id
           LEFT JOIN users u ON u.id = t.user_id
           WHERE s.school_id = %s AND s.deleted_at IS NULL 
           ORDER BY s.class_id, s.name""",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "class_id": r["class_id"],
            "teacher_id": r["teacher_id"],
            "teacher_name": r["teacher_name"],
            "teacher_qualification": r["teacher_qualification"],
        }
        for r in rows
    ]


def get_subjects_by_class(class_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
            s.id, s.name, s.code, s.class_id, s.teacher_id,
            t.qualification as teacher_qualification,
            u.full_name as teacher_name
           FROM subjects s
           LEFT JOIN teachers t ON t.id = s.teacher_id
           LEFT JOIN users u ON u.id = t.user_id
           WHERE s.class_id = %s AND s.school_id = %s AND s.deleted_at IS NULL 
           ORDER BY s.name""",
        (class_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "class_id": r["class_id"],
            "teacher_id": r["teacher_id"],
            "teacher_name": r["teacher_name"],
            "teacher_qualification": r["teacher_qualification"],
        }
        for r in rows
    ]


def update_subject(subject_id: int, name: str, code: str, class_id: int, teacher_id: int, school_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE subjects 
           SET name = %s, code = %s, class_id = %s, teacher_id = %s 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (name, code, class_id, teacher_id, subject_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {
        "id": subject_id,
        "name": name,
        "code": code,
        "class_id": class_id,
        "teacher_id": teacher_id,
        "school_id": school_id
    }


def delete_subject(subject_id: int, school_id: int):
    """Soft delete."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE subjects 
           SET deleted_at = CURRENT_TIMESTAMP 
           WHERE id = %s AND school_id = %s AND deleted_at IS NULL 
           RETURNING id""",
        (subject_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Subject deleted (soft)", "id": subject_id}


def restore_subject(subject_id: int, school_id: int):
    """Restore soft-deleted subject."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE subjects 
           SET deleted_at = NULL 
           WHERE id = %s AND school_id = %s AND deleted_at IS NOT NULL 
           RETURNING id""",
        (subject_id, school_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    if not result:
        return None
    return {"message": "Subject restored", "id": subject_id}