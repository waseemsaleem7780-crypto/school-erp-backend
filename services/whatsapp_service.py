import os
from dotenv import load_dotenv
load_dotenv()

from twilio.rest import Client
from database.db import get_db_connection, get_dict_cursor

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def send_whatsapp_twilio(parent_phone: str, message: str) -> dict:
    """Twilio se WhatsApp message bhejo."""
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)

        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")

        msg = client.messages.create(
            from_=TWILIO_FROM,
            body=message,
            to=f"whatsapp:{parent_phone}"
        )

        return {
            "success": True,
            "message_id": msg.sid,
            "provider": "twilio"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "twilio"}


def send_whatsapp(school_id: int, parent_phone: str, message: str) -> dict:
    return send_whatsapp_twilio(parent_phone, message)


def log_notification(school_id, student_id, parent_phone, event_type, message, status, msg_id=None, error=None):
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