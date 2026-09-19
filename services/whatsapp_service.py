import os
import requests
from dotenv import load_dotenv
load_dotenv()

from database.db import get_db_connection, get_dict_cursor


def get_school_whatsapp_config(school_id: int) -> dict:
    """School ka WhatsApp config dhundo."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT whatsapp_provider, whatsapp_number, whatsapp_account_sid,
                  whatsapp_auth_token, whatsapp_api_key, whatsapp_phone_id
           FROM schools WHERE id = %s AND deleted_at IS NULL""",
        (school_id,)
    )
    school = cursor.fetchone()
    conn.close()
    return dict(school) if school else None


def send_whatsapp(school_id: int, parent_phone: str, message: str) -> dict:
    """School ke apne provider se message bhejo."""
    config = get_school_whatsapp_config(school_id)
    
    if not config:
        return {"success": False, "error": "School not found"}
    
    provider = config.get("whatsapp_provider")
    
    # Agar school mein provider set nahi — default Twilio (env se)
    if not provider:
        provider = os.getenv("WHATSAPP_PROVIDER", "twilio")
    
    if provider == "twilio":
        return send_via_twilio(config, parent_phone, message)
    elif provider == "wab2c":
        return send_via_wab2c(config, parent_phone, message)
    elif provider == "meta":
        return send_via_meta(config, parent_phone, message)
    else:
        return {"success": False, "error": f"Unknown provider: {provider}"}


def send_via_twilio(config: dict, parent_phone: str, message: str) -> dict:
    """Twilio se bhejo — hamesha Sandbox number FROM ke liye."""
    try:
        from twilio.rest import Client
        
        sid = config.get("whatsapp_account_sid") or os.getenv("TWILIO_ACCOUNT_SID")
        token = config.get("whatsapp_auth_token") or os.getenv("TWILIO_AUTH_TOKEN")
        
        # ✅ HAMESHA .env se Twilio ka Sandbox number use karo
        from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        
        if not sid or not token:
            return {"success": False, "error": "Twilio credentials missing", "provider": "twilio"}
        
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        
        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")
        
        client = Client(sid, token)
        msg = client.messages.create(
            from_=from_number,
            body=message,
            to=f"whatsapp:{parent_phone}"
        )
        
        return {"success": True, "message_id": msg.sid, "provider": "twilio"}
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "twilio"}


def send_via_wab2c(config: dict, parent_phone: str, message: str) -> dict:
    """WAB2C se bhejo — school ki keys se."""
    try:
        api_key = config.get("whatsapp_api_key") or os.getenv("WAB2C_API_KEY")
        
        if not api_key:
            return {"success": False, "error": "WAB2C API key missing", "provider": "wab2c"}
        
        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")
        
        url = "https://api.wab2c.com/v1/messages"
        headers = {
            "Authorization": f"Bearer {api_key}",
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
            return {"success": True, "message_id": result.get("id"), "provider": "wab2c"}
        return {"success": False, "error": response.text, "provider": "wab2c"}
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "wab2c"}


def send_via_meta(config: dict, parent_phone: str, message: str) -> dict:
    """Meta Cloud API se bhejo — school ki keys se."""
    try:
        api_key = config.get("whatsapp_api_key")
        phone_id = config.get("whatsapp_phone_id")
        
        if not api_key or not phone_id:
            return {"success": False, "error": "Meta credentials missing", "provider": "meta"}
        
        if not parent_phone.startswith("+"):
            parent_phone = "+" + parent_phone.lstrip("0")
        
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {api_key}",
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
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id"), "provider": "meta"}
        return {"success": False, "error": response.json(), "provider": "meta"}
    except Exception as e:
        return {"success": False, "error": str(e), "provider": "meta"}


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