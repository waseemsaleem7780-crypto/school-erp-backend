from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from utils.dependencies import get_current_user, get_current_school_id, require_super_admin
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/notification", tags=["Notification"])


# ============ NOTIFICATION HISTORY ============
@router.get("/history")
def get_notification_history(
    limit: int = 100,
    event_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """School ke notifications ki history."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    query = """SELECT 
                   nl.id, nl.student_id, nl.parent_phone, nl.event_type,
                   nl.message, nl.status, nl.error_message, nl.sent_at,
                   u.full_name as student_name, s.roll_number
               FROM notification_logs nl
               LEFT JOIN students s ON s.id = nl.student_id
               LEFT JOIN users u ON u.id = s.user_id
               WHERE nl.school_id = %s"""
    params = [school_id]

    if event_type:
        query += " AND nl.event_type = %s"
        params.append(event_type)

    query += " ORDER BY nl.sent_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ============ NOTIFICATION STATS ============
@router.get("/stats")
def get_notification_stats(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Notification stats — sent, failed, by type."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Overall
    cursor.execute(
        """SELECT 
               COUNT(*) as total,
               COUNT(*) FILTER (WHERE status = 'sent') as sent,
               COUNT(*) FILTER (WHERE status = 'failed') as failed
           FROM notification_logs
           WHERE school_id = %s AND sent_at > NOW() - INTERVAL '30 days'""",
        (school_id,)
    )
    overall = cursor.fetchone()

    # By event type
    cursor.execute(
        """SELECT event_type, COUNT(*) as count
           FROM notification_logs
           WHERE school_id = %s AND sent_at > NOW() - INTERVAL '30 days'
           GROUP BY event_type
           ORDER BY count DESC""",
        (school_id,)
    )
    by_type = cursor.fetchall()

    conn.close()

    return {
        "overall": dict(overall) if overall else {},
        "by_type": [dict(r) for r in by_type],
    }


# ============ STUDENT NOTIFICATIONS ============
@router.get("/student/{student_id}")
def get_student_notifications(
    student_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Ek student ke saare notifications."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT id, event_type, message, status, sent_at
           FROM notification_logs
           WHERE student_id = %s AND school_id = %s
           ORDER BY sent_at DESC LIMIT %s""",
        (student_id, school_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============ SUPER ADMIN: ALL SCHOOLS STATS ============
@router.get("/admin/stats")
def super_admin_stats(current_user: dict = Depends(require_super_admin)):
    """Super admin: saare schools ke notification stats."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        """SELECT 
               s.id as school_id,
               s.name as school_name,
               COUNT(nl.id) as total_notifications,
               COUNT(nl.id) FILTER (WHERE nl.status = 'sent') as sent,
               COUNT(nl.id) FILTER (WHERE nl.status = 'failed') as failed
           FROM schools s
           LEFT JOIN notification_logs nl ON nl.school_id = s.id 
               AND nl.sent_at > NOW() - INTERVAL '30 days'
           WHERE s.deleted_at IS NULL
           GROUP BY s.id, s.name
           ORDER BY total_notifications DESC"""
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============ RETRY FAILED ============
@router.post("/retry/{notification_id}")
def retry_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Failed notification dobara bhejo."""
    from services.whatsapp_service import send_whatsapp

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT * FROM notification_logs 
           WHERE id = %s AND school_id = %s AND status = 'failed'""",
        (notification_id, school_id)
    )
    notif = cursor.fetchone()

    if not notif:
        conn.close()
        raise HTTPException(404, "Failed notification not found")

    # Dobara bhejo
    result = send_whatsapp(school_id, notif["parent_phone"], notif["message"])

    # Update
    cursor.execute(
        """UPDATE notification_logs 
           SET status = %s, error_message = %s, sent_at = NOW()
           WHERE id = %s""",
        ("sent" if result["success"] else "failed", result.get("error"), notification_id)
    )
    conn.commit()
    conn.close()

    return {"success": result["success"], "message_id": result.get("message_id")}