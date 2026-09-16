from database.db import get_db_connection, get_dict_cursor

def create_assignment(student_id: int, subject_id: int, teacher_id: int, title: str, description: str, deadline: str, file_path: str = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO assignment (student_id, subject_id, teacher_id, title, description, deadline, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
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

def get_assignments_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, student_id, subject_id, teacher_id, title, description, deadline, file_path, created_at FROM assignment WHERE student_id = %s ORDER BY deadline ASC",
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
def update_assignment(assignment_id: int, title: str, description: str, deadline: str, file_path: str = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "UPDATE assignment SET title = %s, description = %s, deadline = %s, file_path = %s WHERE id = %s RETURNING id",
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
def delete_assignment(assignment_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("DELETE FROM assignment WHERE id = %s RETURNING id", (assignment_id,))
    result = cursor.fetchone()
    conn.commit()
    conn.close()
    
    if not result:
        return None
    
    return {"message": "Assignment deleted", "id": assignment_id}