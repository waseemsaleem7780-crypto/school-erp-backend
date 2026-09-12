from database.db import get_db_connection, get_dict_cursor

def create_setting(setting_key: str, setting_value: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO school_settings (setting_key, setting_value) VALUES (%s, %s) RETURNING id",
        (setting_key, setting_value)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "setting_key": setting_key,
        "setting_value": setting_value
    }

def get_all_settings():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, setting_key, setting_value FROM school_settings ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "setting_key": row["setting_key"],
            "setting_value": row["setting_value"]
        }
        for row in rows
    ]

def get_setting_by_key(setting_key: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, setting_key, setting_value FROM school_settings WHERE setting_key = %s",
        (setting_key,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "setting_key": row["setting_key"],
            "setting_value": row["setting_value"]
        }
    return None