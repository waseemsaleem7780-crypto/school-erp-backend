from database.db import get_db_connection, get_dict_cursor

def create_assignment(student_id: int, subject_id: int, teacher_id: int, title: str, description: str, deadline: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO assignment (student_id, subject_id, teacher_id, title, description, deadline) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (student_id, subject_id, teacher_id, title, description, deadline)
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
        "deadline": deadline
    }

def get_assignments_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, student_id, subject_id, teacher_id, title, description, deadline, created_at FROM assignment WHERE student_id = %s ORDER BY deadline ASC",
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
            "deadline": row["deadline"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]