from database.db import get_db_connection, get_dict_cursor


def log_action(user_id: int, school_id: int, action: str, details: dict = None, ip: str = None, user_agent: str = None):
    """Audit log save karo."""
    try:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """INSERT INTO audit_logs (user_id, school_id, action, details, ip_address, user_agent)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, school_id, action, details, ip, user_agent)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log failed: {e}")


def get_audit_logs(school_id: int = None, user_id: int = None, limit: int = 100):
    """Audit logs fetch karo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if school_id:
        query += " AND school_id = %s"
        params.append(school_id)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
