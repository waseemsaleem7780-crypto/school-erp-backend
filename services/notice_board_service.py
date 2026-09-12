from database.db import get_db_connection, get_dict_cursor

def create_notice(title: str, context: str, class_id: int, section_id: int, posted_by: int, target_audience_id: int, is_active: bool):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO notice_board (title, context, class_id, section_id, posted_by, target_audience_id, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (title, context, class_id, section_id, posted_by, target_audience_id, is_active)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "title": title,
        "context": context,
        "class_id": class_id,
        "section_id": section_id,
        "posted_by": posted_by,
        "target_audience_id": target_audience_id,
        "is_active": is_active
    }

def get_notices_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, title, context, class_id, section_id, posted_by, posted_at, target_audience_id, is_active FROM notice_board WHERE class_id = %s ORDER BY posted_at DESC",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "context": row["context"],
            "class_id": row["class_id"],
            "section_id": row["section_id"],
            "posted_by": row["posted_by"],
            "posted_at": row["posted_at"],
            "target_audience_id": row["target_audience_id"],
            "is_active": row["is_active"]
        }
        for row in rows
    ]