from database.db import get_db_connection, get_dict_cursor

def create_exam(name: str, class_id: int, subject_id: int, exam_date: str, total_marks: int, passing_marks: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO exam (name, class_id, subject_id, exam_date, total_marks, passing_marks) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (name, class_id, subject_id, exam_date, total_marks, passing_marks)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "name": name,
        "class_id": class_id,
        "subject_id": subject_id,
        "exam_date": exam_date,
        "total_marks": total_marks,
        "passing_marks": passing_marks
    }

def get_exams_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, name, class_id, subject_id, exam_date, total_marks, passing_marks FROM exam WHERE class_id = %s ORDER BY exam_date DESC",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "class_id": row["class_id"],
            "subject_id": row["subject_id"],
            "exam_date": row["exam_date"],
            "total_marks": row["total_marks"],
            "passing_marks": row["passing_marks"]
        }
        for row in rows
    ]