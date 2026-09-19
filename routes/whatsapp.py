from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.whatsapp_service import send_whatsapp, log_notification
from utils.dependencies import get_current_user, get_current_school_id, require_super_admin
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


class TestMessageRequest(BaseModel):
    phone: str
    message: Optional[str] = "Test message from School ERP ✅"


class UpdateConfigRequest(BaseModel):
    whatsapp_number: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None


# ============ TEST MESSAGE ============
@router.post("/test")
def test_whatsapp(
    request: TestMessageRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """School ka WhatsApp config test karo."""
    result = send_whatsapp(school_id, request.phone, request.message)

    if not result["success"]:
        raise HTTPException(400, f"WhatsApp failed: {result.get('error')}")

    return {
        "success": True,
        "message": "Test message sent successfully",
        "message_id": result.get("message_id")
    }


# ============ GET CONFIG (SCHOOL ADMIN) ============
@router.get("/config")
def get_whatsapp_config(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """School ka WhatsApp config dekho."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT whatsapp_number, whatsapp_phone_id,
                  CASE WHEN whatsapp_api_key IS NOT NULL THEN 'configured' ELSE 'not_configured' END as api_key_status
           FROM schools WHERE id = %s""",
        (school_id,)
    )
    config = cursor.fetchone()
    conn.close()

    if not config:
        raise HTTPException(404, "School not found")

    return dict(config)


# ============ UPDATE CONFIG (SCHOOL ADMIN) ============
@router.put("/config")
def update_whatsapp_config(
    request: UpdateConfigRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """School apna WhatsApp config update kare."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    updates = []
    params = []

    if request.whatsapp_number is not None:
        updates.append("whatsapp_number = %s")
        params.append(request.whatsapp_number)
    if request.whatsapp_api_key is not None:
        updates.append("whatsapp_api_key = %s")
        params.append(request.whatsapp_api_key)
    if request.whatsapp_phone_id is not None:
        updates.append("whatsapp_phone_id = %s")
        params.append(request.whatsapp_phone_id)

    if not updates:
        conn.close()
        raise HTTPException(400, "No fields to update")

    params.append(school_id)
    query = f"UPDATE schools SET {', '.join(updates)} WHERE id = %s RETURNING id"

    cursor.execute(query, tuple(params))
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        raise HTTPException(404, "School not found")

    return {"message": "WhatsApp config updated", "school_id": school_id}


# ============ SUPER ADMIN: UPDATE ANY SCHOOL ============
@router.put("/config/{school_id}")
def super_admin_update_config(
    school_id: int,
    request: UpdateConfigRequest,
    current_user: dict = Depends(require_super_admin)
):
    """Super admin kisi bhi school ka WhatsApp config update kare."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    updates = []
    params = []

    if request.whatsapp_number is not None:
        updates.append("whatsapp_number = %s")
        params.append(request.whatsapp_number)
    if request.whatsapp_api_key is not None:
        updates.append("whatsapp_api_key = %s")
        params.append(request.whatsapp_api_key)
    if request.whatsapp_phone_id is not None:
        updates.append("whatsapp_phone_id = %s")
        params.append(request.whatsapp_phone_id)

    if not updates:
        conn.close()
        raise HTTPException(400, "No fields to update")

    params.append(school_id)
    query = f"UPDATE schools SET {', '.join(updates)} WHERE id = %s RETURNING id"

    cursor.execute(query, tuple(params))
    result = cursor.fetchone()
    conn.commit()
    conn.close()

    if not result:
        raise HTTPException(404, "School not found")

    return {"message": "WhatsApp config updated", "school_id": school_id}