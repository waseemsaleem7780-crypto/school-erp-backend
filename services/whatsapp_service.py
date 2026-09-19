import os
from dotenv import load_dotenv
load_dotenv()

from database.db import get_db_connection, get_dict_cursor

# ============ PROVIDER SETTING ============
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "twilio")

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# WAB2C credentials
WAB2C_API_KEY = os.getenv("WAB2C_API_KEY")
WAB2C_HOST = os.getenv("WAB2C_HOST", "https://api.wab2c.com")


# ============ TWILIO PROVIDER ============
def send_via_twilio(parent_phone: str, message: str) -> dict:
    """Twilio se WhatsApp bhejo."""
    try:
        from twilio.rest import Client
        
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


# ============ WAB2C PROVIDER ============
def send_via_wab2c(parent_phone: str, message: str) -> dict:
    """WAB2C se WhatsApp bhejo."""
    try:
        import requests
        
        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")
        
        url = f"{WAB2C_HOST}/v1/messages"
        
        headers = {
            "Authorization": f"Bearer {WAB2C_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "to": parent_phone,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message_id": result.get("id"),
                "provider": "wab2c"
            }
        return {"success": False, "error": response.text, "provider": "wab2c"}
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "wab2c"}


# ============ MAIN FUNCTION (Provider Switch) ============
def send_whatsapp(school_id: int, parent_phone: str, message: str) -> dict:
    """
    WhatsApp message bhejo — provider ke hisaab se.
    
    .env mein WHATSAPP_PROVIDER set karo:
    - 'twilio' = Twilio (testing)
    - 'wab2c' = WAB2C (production)
    """
    if WHATSAPP_PROVIDER == "wab2c":
        return send_via_wab2c(parent_phone, message)
    else:
        return send_via_twilio(parent_phone, message)


# ============ LOG ============
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