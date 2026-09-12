from database.db import get_db_connection, get_dict_cursor

def create_study_material(class_id: int, subject_id: int, section_id: int, teacher_id: int, title: str, description: str, file_path: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO study_material (class_id, subject_id, section_id, teacher_id, title, description, file_path) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (class_id, subject_id, section_id, teacher_id, title, description, file_path)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "class_id": class_id,
        "subject_id": subject_id,
        "section_id": section_id,
        "teacher_id": teacher_id,
        "title": title,
        "description": description,
        "file_path": file_path
    }

def get_study_material_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, class_id, subject_id, section_id, teacher_id, title, description, file_path, uploaded_at FROM study_material WHERE class_id = %s ORDER BY uploaded_at DESC",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "class_id": row["class_id"],
            "subject_id": row["subject_id"],
            "section_id": row["section_id"],
            "teacher_id": row["teacher_id"],
            "title": row["title"],
            "description": row["description"],
            "file_path": row["file_path"],
            "uploaded_at": row["uploaded_at"]
        }
        for row in rows
    ]