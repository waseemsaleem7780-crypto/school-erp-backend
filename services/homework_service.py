from database.db import get_db_connection, get_dict_cursor


def create_homework(student_id: int, subject_id: int, teacher_id: int, title: str, description: str, deadline: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO homework (student_id, subject_id, teacher_id, title, description, deadline) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
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


def get_homework_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT h.id, h.student_id, h.subject_id, h.teacher_id, h.title, h.description, h.deadline, h.created_at,
                  s.name AS subject_name,
                  t.qualification AS teacher_name
           FROM homework h
           LEFT JOIN subjects s ON s.id = h.subject_id
           LEFT JOIN teachers t ON t.id = h.teacher_id
           WHERE h.student_id = %s 
           ORDER BY h.deadline ASC""",
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
            "deadline": str(row["deadline"]) if row["deadline"] else None,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
            "subject_name": row["subject_name"],
            "teacher_name": row["teacher_name"],
        }
        for row in rows
    ]


def get_homework_by_class(class_id: int):
    """Class ki saari homework — ek hi query mein, duplicates ke saath."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT DISTINCT
              h.id, h.student_id, h.subject_id, h.teacher_id, 
              h.title, h.description, h.deadline, h.created_at,
              s.name AS subject_name,
              t.qualification AS teacher_name,
              st.roll_number AS student_roll
           FROM homework h
           LEFT JOIN subjects s ON s.id = h.subject_id
           LEFT JOIN teachers t ON t.id = h.teacher_id
           LEFT JOIN students st ON st.id = h.student_id
           WHERE st.class_id = %s
           ORDER BY h.deadline ASC, h.id DESC""",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Unique homework (title + subject + deadline same → ek hi dikhega)
    seen = set()
    unique = []
    for row in rows:
        key = f"{row['title']}|{row['subject_id']}|{row['deadline']}"
        if key in seen:
            continue
        seen.add(key)
        unique.append({
            "id": row["id"],
            "student_id": row["student_id"],
            "subject_id": row["subject_id"],
            "teacher_id": row["teacher_id"],
            "title": row["title"],
            "description": row["description"],
            "deadline": str(row["deadline"]) if row["deadline"] else None,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
            "subject_name": row["subject_name"],
            "teacher_name": row["teacher_name"],
        })
    return unique