import os
import requests
from dotenv import load_dotenv
load_dotenv()

from database.db import get_db_connection, get_dict_cursor


def get_school_whatsapp_config(school_id: int = None) -> dict:
    """
    Single-school setup — env se config lo.
    school_id parameter ignore hota hai (compatibility ke liye rakha).
    """
    return {
        "whatsapp_provider": os.getenv("WHATSAPP_PROVIDER", "twilio"),
        "whatsapp_account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "whatsapp_auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
        "whatsapp_api_key": os.getenv("WAB2C_API_KEY"),
        "whatsapp_phone_id": os.getenv("META_PHONE_ID"),
        "whatsapp_number": os.getenv("TWILIO_WHATSAPP_FROM"),
    }


def send_whatsapp(school_id, parent_phone: str, message: str) -> dict:
    """WhatsApp message bhejo. school_id optional hai (single-school)."""
    config = get_school_whatsapp_config(school_id)
    provider = config.get("whatsapp_provider") or "twilio"

    if provider == "twilio":
        return send_via_twilio(config, parent_phone, message)
    elif provider == "wab2c":
        return send_via_wab2c(config, parent_phone, message)
    elif provider == "meta":
        return send_via_meta(config, parent_phone, message)
    else:
        return {"success": False, "error": f"Unknown provider: {provider}"}


def send_via_twilio(config: dict, parent_phone: str, message: str) -> dict:
    """Twilio se message bhejo."""
    try:
        from twilio.rest import Client

        sid = config.get("whatsapp_account_sid") or os.getenv("TWILIO_ACCOUNT_SID")
        token = config.get("whatsapp_auth_token") or os.getenv("TWILIO_AUTH_TOKEN")
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
    """WAB2C se message bhejo."""
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
    """Meta Cloud API se message bhejo."""
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
    """Notification log save karo (agent_logs table use karta hai)."""
    try:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """INSERT INTO agent_logs
               (guardian_id, student_id, question, answer, intent, tools_used, response_time_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                None,
                student_id,
                f"[{event_type}] to {parent_phone}",
                message[:500],
                "notification",
                status,
                None,
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Notification log failed: {e}")
