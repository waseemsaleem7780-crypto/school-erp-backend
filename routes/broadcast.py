from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from services.broadcast_service import send_broadcast
from utils.dependencies import get_current_user, get_current_school_id
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/broadcast", tags=["Broadcast"])


class BroadcastRequest(BaseModel):
    title: str
    message: str
    target_type: str  # 'all', 'class', 'section', 'students'
    target_id: Optional[int] = None


@router.post("/send")
def send_broadcast_message(
    request: BroadcastRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """One-click broadcast to hundreds of parents."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """INSERT INTO broadcasts (school_id, title, message, target_type, target_id, created_by)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (school_id, request.title, request.message, request.target_type,
         request.target_id, current_user.get("user_id") or current_user.get("id"))
    )
    broadcast_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()

    background_tasks.add_task(
        send_broadcast, broadcast_id, school_id,
        request.message, request.target_type, request.target_id
    )

    return {
        "broadcast_id": broadcast_id,
        "message": "Broadcast started. Messages are being sent in background.",
        "status": "pending"
    }


@router.get("/{broadcast_id}/status")
def get_broadcast_status(broadcast_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT * FROM broadcasts WHERE id = %s", (broadcast_id,))
    broadcast = cursor.fetchone()
    conn.close()

    if not broadcast:
        raise HTTPException(404, "Broadcast not found")

    return dict(broadcast)


@router.get("/history")
def get_broadcast_history(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT * FROM broadcasts WHERE school_id = %s ORDER BY created_at DESC LIMIT 50",
        (school_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]