from database.db import get_db_connection, get_dict_cursor


def create_assignment(student_id: int, subject_id: int, teacher_id: int, 
                     title: str, description: str, deadline: str, 
                     file_path: str = None, school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    # ✅ Check karo ke student is school ka hai
    if school_id:
        cursor.execute(
            "SELECT id FROM students WHERE id = %s AND school_id = %s AND deleted_at IS NULL",
            (student_id, school_id)
        )
        if not cursor.fetchone():
            conn.close()
            raise ValueError("Student not found in this school")
    
    cursor.execute(
        """INSERT INTO assignment (student_id, subject_id, teacher_id, title, description, deadline, file_path) 
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (student_id, subject_id, teacher_id, title, description, deadline, file_path)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "student_id": student_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "title": title,
        "description": description,
        "deadline": str(deadline),
        "file_path": file_path,
    }


def get_all_assignments(school_id: int = None):
    """Sirf is school ki assignments."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    if school_id:
        # ✅ Students ke through filter karo
        cursor.execute(
            """SELECT a.id, a.student_id, a.subject_id, a.teacher_id, 
                      a.title, a.description, a.deadline, a.file_path, a.created_at
               FROM assignment a
               JOIN students s ON s.id = a.student_id
               WHERE s.school_id = %s AND s.deleted_at IS NULL
               ORDER BY a.created_at DESC""",
            (school_id,)
        )
    else:
        cursor.execute(
            """SELECT id, student_id, subject_id, teacher_id, title, description, 
                      deadline, file_path, created_at 
               FROM assignment ORDER BY created_at DESC"""
        )
    
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "subject_id": row["subject_id"],
            "teacher_id": row["teacher_id"],
            "title": row["title"],
            "description": row["description"],
            "deadline": str(row["deadline"]),
            "file_path": row.get("file_path"),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    ]


def get_assignments_by_student(student_id: int, school_id: int = None):
    """Ek student ki assignments — sirf is school ka."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    if school_id:
        # ✅ Pehle check karo student is school ka hai
        cursor.execute(
            "SELECT id FROM students WHERE id = %s AND school_id = %s AND deleted_at IS NULL",
            (student_id, school_id)
        )
        if not cursor.fetchone():
            conn.close()
            return []
    
    cursor.execute(
        """SELECT id, student_id, subject_id, teacher_id, title, description, 
                  deadline, file_path, created_at 
           FROM assignment WHERE student_id = %s ORDER BY deadline ASC""",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "subject_id": row["subject_id"],
            "teacher_id": row["teacher_id"],
            "title": row["title"],
            "description": row["description"],
            "deadline": str(row["deadline"]),
            "file_path": row.get("file_path"),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    ]


def update_assignment(assignment_id: int, title: str, description: str, 
                     deadline: str, file_path: str = None, school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    if school_id:
        # ✅ Check karo assignment is school ki hai
        cursor.execute(
            """SELECT a.id FROM assignment a
               JOIN students s ON s.id = a.student_id
               WHERE a.id = %s AND s.school_id = %s""",
            (assignment_id, school_id)
        )
        if not cursor.fetchone():
            conn.close()
            return None
    
    cursor.execute(
        """UPDATE assignment SET title = %s, description = %s, deadline = %s, file_path = %s 
           WHERE id = %s RETURNING id""",
        (title, description, deadline, file_path, assignment_id)
    )
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {
        "id": assignment_id,
        "title": title,
        "description": description,
        "deadline": str(deadline),
        "file_path": file_path,
    }


def delete_assignment(assignment_id: int, school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    if school_id:
        # ✅ Check karo assignment is school ki hai
        cursor.execute(
            """SELECT a.id FROM assignment a
               JOIN students s ON s.id = a.student_id
               WHERE a.id = %s AND s.school_id = %s""",
            (assignment_id, school_id)
        )
        if not cursor.fetchone():
            conn.close()
            return None
    
    cursor.execute("DELETE FROM assignment WHERE id = %s RETURNING id", (assignment_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"message": "Assignment deleted", "id": assignment_id}