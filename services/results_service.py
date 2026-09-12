from database.db import get_db_connection, get_dict_cursor

def create_result(exam_id: int, student_id: int, subject_id: int, marks_obtained: float, grade: str, remarks: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO results (exam_id, student_id, subject_id, marks_obtained, grade, remarks) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (exam_id, student_id, subject_id, marks_obtained, grade, remarks)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "exam_id": exam_id,
        "student_id": student_id,
        "subject_id": subject_id,
        "marks_obtained": marks_obtained,
        "grade": grade,
        "remarks": remarks
    }

def get_results_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, exam_id, student_id, subject_id, marks_obtained, grade, remarks FROM results WHERE student_id = %s ORDER BY exam_id DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "exam_id": row["exam_id"],
            "student_id": row["student_id"],
            "subject_id": row["subject_id"],
            "marks_obtained": row["marks_obtained"],
            "grade": row["grade"],
            "remarks": row["remarks"]
        }
        for row in rows
    ]