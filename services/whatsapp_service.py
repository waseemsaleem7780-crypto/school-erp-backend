import requests
from database.db import get_db_connection, get_dict_cursor


def send_whatsapp(school_id: int, parent_phone: str, message: str) -> dict:
    """School ke apne WhatsApp number se message bhejo."""
    try:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """SELECT name, whatsapp_number, whatsapp_api_key, whatsapp_phone_id 
               FROM schools WHERE id = %s AND deleted_at IS NULL""",
            (school_id,)
        )
        school = cursor.fetchone()
        conn.close()

        if not school:
            return {"success": False, "error": "School not found"}
        if not school["whatsapp_api_key"] or not school["whatsapp_phone_id"]:
            return {"success": False, "error": "WhatsApp not configured for this school"}

        # Number format
        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")

        url = f"https://graph.facebook.com/v18.0/{school['whatsapp_phone_id']}/messages"
        headers = {
            "Authorization": f"Bearer {school['whatsapp_api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": parent_phone,
            "type": "text",
            "text": {"body": message}
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
        else:
            return {"success": False, "error": response.json()}

    except Exception as e:
        return {"success": False, "error": str(e)}


def log_notification(school_id, student_id, parent_phone, event_type, message, status, msg_id=None, error=None):
    """Notification log save karo."""
    try:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """INSERT INTO notification_logs 
               (school_id, student_id, parent_phone, event_type, message, status, whatsapp_message_id, error_message)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (school_id, student_id, parent_phone, event_type, message, status, msg_id, error)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Notification log failed: {e}")