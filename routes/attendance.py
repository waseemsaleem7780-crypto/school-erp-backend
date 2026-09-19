from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.attendance_service import (
    bulk_mark_attendance,
    get_attendance_by_date_and_class,
    get_attendance_history,
    get_attendance_stats,
)
from services.notification_service import notify_absent
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/attendance", tags=["Attendance"])


class AttendanceItem(BaseModel):
    student_id: int
    date: str
    status: str


class BulkAttendanceRequest(BaseModel):
    records: List[AttendanceItem]


# ✅ Single attendance (frontend /api/attendance/ ke liye)
class SingleAttendance(BaseModel):
    student_id: int
    date: str
    status: str


@router.post("/")
def mark_single(
    record: SingleAttendance,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Single student ki attendance mark karo."""
    marked_by = current_user.get("id") or current_user.get("user_id")
    result = bulk_mark_attendance([record.dict()], marked_by, school_id)

    # ✅ WhatsApp notification — try/except mein wrap karo
    if record.status.lower() == "absent":
        try:
            notify_absent(
                school_id=school_id,
                student_id=record.student_id,
                date=record.date
            )
        except Exception as e:
            print(f"WhatsApp notification failed: {e}")
            # Attendance already saved — error ignore karo

    return result


@router.post("/bulk")
def mark_bulk(
    request: BulkAttendanceRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Multiple students ki attendance ek saath mark karo."""
    records = [r.dict() for r in request.records]
    marked_by = current_user.get("id") or current_user.get("user_id")
    result = bulk_mark_attendance(records, marked_by, school_id)

    # ✅ Absent students ko WhatsApp bhejo
    for record in records:
        if record["status"].lower() == "absent":
            try:
                notify_absent(
                    school_id=school_id,
                    student_id=record["student_id"],
                    date=record["date"]
                )
            except Exception as e:
                print(f"WhatsApp notification failed for {record['student_id']}: {e}")

    return result


@router.get("/date/{date}/class/{class_id}")
def get_by_date_class(
    date: str,
    class_id: int,
    section_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_attendance_by_date_and_class(date, class_id, school_id, section_id)


@router.get("/history/{student_id}")
def get_history(
    student_id: int,
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_attendance_history(student_id, school_id, limit)


@router.get("/stats/{date}")
def get_stats(
    date: str,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_attendance_stats(date, school_id)