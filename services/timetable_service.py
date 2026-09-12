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
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, class_id, section_id, subject_id, teacher_id, day_of_week, start_time, end_time FROM timetable WHERE class_id = %s ORDER BY day_of_week",
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
            "start_time": row["start_time"],
            "end_time": row["end_time"]
        }
        for row in rows
    ]