from database.db import get_db_connection, get_dict_cursor


def create_timetable(class_id: int, section_id: int, subject_id: int, teacher_id: int, day_of_week: str, start_time: str, end_time: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO timetable (class_id, section_id, subject_id, teacher_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (class_id, section_id, subject_id, teacher_id, day_of_week, start_time, end_time)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "class_id": class_id,
        "section_id": section_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time
    }


def get_timetable_by_class(class_id: int):
    """Class ki timetable — subject aur teacher ke NAAM ke saath."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
              t.id, 
              t.class_id, 
              t.section_id, 
              t.subject_id, 
              t.teacher_id, 
              t.day_of_week, 
              t.start_time, 
              t.end_time,
              s.name AS subject_name,
              COALESCE(u.full_name, tch.qualification) AS teacher_name
           FROM timetable t
           LEFT JOIN subjects s ON s.id = t.subject_id
           LEFT JOIN teachers tch ON tch.id = t.teacher_id
           LEFT JOIN users u ON u.id = tch.user_id
           WHERE t.class_id = %s 
           ORDER BY t.day_of_week, t.start_time""",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "class_id": row["class_id"],
            "section_id": row["section_id"],
            "subject_id": row["subject_id"],
            "teacher_id": row["teacher_id"],
            "day_of_week": row["day_of_week"],
            "start_time": str(row["start_time"]),
            "end_time": str(row["end_time"]),
            "subject_name": row["subject_name"] or f"Subject #{row['subject_id']}",
            "teacher_name": row["teacher_name"] or f"Teacher #{row['teacher_id']}",
        }
        for row in rows
    ]