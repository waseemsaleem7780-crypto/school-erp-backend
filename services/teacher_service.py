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
    """
    Teachers with name + email + phone + assigned classes.
    ✅ NEW: Har teacher ke saath assigned_classes bhi aayengi.
    """
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    # ✅ Main query — teachers + user info
    cursor.execute(
        """SELECT 
            t.id, 
            t.user_id, 
            t.qualification, 
            t.hired_date,
            u.full_name as teacher_name,
            u.email as teacher_email,
            u.phone as teacher_phone
           FROM teachers t
           LEFT JOIN users u ON u.id = t.user_id
           WHERE t.school_id = %s AND t.deleted_at IS NULL 
           ORDER BY t.id""",
        (school_id,)
    )
    rows = cursor.fetchall()

    # ✅ Har teacher ki classes fetch karo
    result = []
    for row in rows:
        teacher_id = row["id"]
        
        # Assigned classes nikalo
        cursor.execute(
            """SELECT 
                ta.class_id,
                c.name AS class_name
               FROM teacher_assignments ta
               JOIN classes c ON c.id = ta.class_id
               WHERE ta.teacher_id = %s AND ta.school_id = %s
               ORDER BY c.name""",
            (teacher_id, school_id)
        )
        class_rows = cursor.fetchall()
        
        assigned_classes = [
            {"class_id": cr["class_id"], "class_name": cr["class_name"]}
            for cr in class_rows
        ]

        result.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "qualification": row["qualification"],
            "hired_date": str(row["hired_date"]) if row["hired_date"] else None,
            "teacher_name": row["teacher_name"] or f"Teacher #{row['id']}",
            "teacher_email": row["teacher_email"] or "—",
            "teacher_phone": row["teacher_phone"] or "—",
            "assigned_classes": assigned_classes,   # ✅ NEW
            "assigned_class_ids": [c["class_id"] for c in assigned_classes],   # ✅ Shortcut
        })

    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════
#  CLASS ASSIGNMENT HELPERS
# ═══════════════════════════════════════════════════════════════

def get_teacher_assignments(teacher_id: int, school_id: int):
    """Ek teacher ki assigned classes nikalo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
            ta.id,
            ta.class_id,
            ta.section_id,
            ta.subject_id,
            c.name AS class_name
           FROM teacher_assignments ta
           JOIN classes c ON c.id = ta.class_id
           WHERE ta.teacher_id = %s AND ta.school_id = %s
           ORDER BY c.name""",
        (teacher_id, school_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_teacher_assignments(teacher_id: int, class_ids: list, school_id: int):
    """
    Teacher ki classes set karo — purani hatao, nayi add karo.
    Return: assigned class IDs list.
    """
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # ✅ Purani assignments delete karo
        cursor.execute(
            "DELETE FROM teacher_assignments WHERE teacher_id = %s AND school_id = %s",
            (teacher_id, school_id)
        )

        # ✅ Nayi assignments add karo
        assigned = []
        for class_id in class_ids:
            # Check karo class exist karta hai
            cursor.execute(
                "SELECT id FROM classes WHERE id = %s AND school_id = %s",
                (class_id, school_id)
            )
            if not cursor.fetchone():
                continue  # Skip invalid class

            cursor.execute(
                """INSERT INTO teacher_assignments 
                   (teacher_id, class_id, school_id) 
                   VALUES (%s, %s, %s) RETURNING id""",
                (teacher_id, class_id, school_id)
            )
            assigned.append(class_id)

        conn.commit()
        return assigned

    except Exception as e:
        conn.rollback()
        print(f"set_teacher_assignments error: {e}")
        raise e
    finally:
        conn.close()


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