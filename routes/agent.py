from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from services.agent_brain import ask_agent
import os


router = APIRouter(prefix="/agent", tags=["Agent"])


def _normalize_phone(phone: str) -> str:
    """Twilio ka 'whatsapp:+923001234567' ko '+923001234567' banao."""
    if not phone:
        return ""
    phone = phone.replace("whatsapp:", "").strip()
    if not phone.startswith("+"):
        phone = "+" + phone.lstrip("0")
    return phone


def _escape_xml(text: str) -> str:
    """XML mein special characters escape karo."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Twilio WhatsApp webhook."""
    try:
        form = await request.form()
        from_raw = form.get("From", "")
        body = form.get("Body", "").strip()

        from_phone = _normalize_phone(from_raw)

        print(f"WhatsApp from {from_phone}: {body[:80]}")

        if not body:
            return PlainTextResponse("", media_type="text/xml")

        result = ask_agent(from_phone, body)
        answer = result.get("answer", "Sorry, jawab nahi de saka.")

        print(f"Reply to {from_phone}: {answer[:80]}")

        twiml = '<?xml version="1.0" encoding="UTF-8"?>'
        twiml += "<Response><Message>" + _escape_xml(answer) + "</Message></Response>"

        return PlainTextResponse(twiml, media_type="text/xml")

    except Exception as e:
        print(f"Webhook error: {e}")
        fallback = '<?xml version="1.0" encoding="UTF-8"?>'
        fallback += "<Response><Message>Sorry, technical issue. Thodi der baad try karein.</Message></Response>"
        return PlainTextResponse(fallback, media_type="text/xml")


@router.get("/whatsapp/webhook")
async def whatsapp_webhook_verify():
    """Health check."""
    return {
        "status": "ok",
        "message": "Agent WhatsApp webhook is live. POST Twilio messages here.",
    }


@router.post("/chat")
async def chat_test(request: Request):
    """Direct test endpoint."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    phone = data.get("phone")
    question = data.get("question")

    if not phone or not question:
        raise HTTPException(status_code=400, detail="phone aur question dono chahiye")

    result = ask_agent(phone, question)
    return result
