import time
from database.db import get_db_connection, get_dict_cursor
from services.whatsapp_service import send_whatsapp


def send_broadcast(broadcast_id, school_id, message, target_type, target_id):
    """Background task: 1000s messages ek saath bhejo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("UPDATE broadcasts SET status = 'sending' WHERE id = %s", (broadcast_id,))
    conn.commit()

    # Recipients dhundo
    if target_type == "all":
        cursor.execute(
            """SELECT DISTINCT COALESCE(g.whatsapp_number, g.phone_number) as parent_phone, g.student_id
               FROM guardians g
               JOIN students s ON s.id = g.student_id
               WHERE s.school_id = %s AND COALESCE(g.whatsapp_number, g.phone_number) IS NOT NULL""",
            (school_id,)
        )
    elif target_type == "class":
        cursor.execute(
            """SELECT DISTINCT COALESCE(g.whatsapp_number, g.phone_number) as parent_phone, g.student_id
               FROM guardians g
               JOIN students s ON s.id = g.student_id
               WHERE s.school_id = %s AND s.class_id = %s
                 AND COALESCE(g.whatsapp_number, g.phone_number) IS NOT NULL""",
            (school_id, target_id)
        )
    elif target_type == "section":
        cursor.execute(
            """SELECT DISTINCT COALESCE(g.whatsapp_number, g.phone_number) as parent_phone, g.student_id
               FROM guardians g
               JOIN students s ON s.id = g.student_id
               WHERE s.school_id = %s AND s.section_id = %s
                 AND COALESCE(g.whatsapp_number, g.phone_number) IS NOT NULL""",
            (school_id, target_id)
        )
    else:
        cursor.execute(
            """SELECT DISTINCT COALESCE(g.whatsapp_number, g.phone_number) as parent_phone, g.student_id
               FROM guardians g
               WHERE g.student_id = %s AND COALESCE(g.whatsapp_number, g.phone_number) IS NOT NULL""",
            (target_id,)
        )

    recipients = cursor.fetchall()
    total = len(recipients)

    cursor.execute("UPDATE broadcasts SET total_recipients = %s WHERE id = %s", (total, broadcast_id))
    conn.commit()

    sent_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            result = send_whatsapp(school_id, recipient["parent_phone"], message)
            if result["success"]:
                sent_count += 1
            else:
                failed_count += 1
            time.sleep(1)  # Rate limit
        except Exception as e:
            failed_count += 1
            print(f"Failed for {recipient['parent_phone']}: {e}")

    cursor.execute(
        """UPDATE broadcasts SET status = 'completed', sent_count = %s, failed_count = %s, completed_at = NOW()
           WHERE id = %s""",
        (sent_count, failed_count, broadcast_id)
    )
    conn.commit()
    conn.close()

    return {"broadcast_id": broadcast_id, "total": total, "sent": sent_count, "failed": failed_count}
