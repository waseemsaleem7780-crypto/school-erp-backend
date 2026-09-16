from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.attendance_service import (
    mark_attendance,
    bulk_mark_attendance,
    get_attendance_by_date_and_class,
    get_attendance_history,
    get_attendance_stats,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


class AttendanceItem(BaseModel):
    student_id: int
    date: str
    status: str
    class_id: Optional[int] = None
    section_id: Optional[int] = None


class BulkAttendanceRequest(BaseModel):
    records: List[AttendanceItem]


@router.post("/mark")
def mark_single(
    item: AttendanceItem,
    current_user: dict = Depends(get_current_user)
):
    return mark_attendance(
        item.student_id, item.date, item.status, item.class_id, item.section_id
    )


@router.post("/bulk")
def mark_bulk(
    request: BulkAttendanceRequest,
    current_user: dict = Depends(get_current_user)
):
    records = [r.dict() for r in request.records]
    return bulk_mark_attendance(records)


@router.get("/date/{date}/class/{class_id}")
def get_by_date_class(
    date: str,
    class_id: int,
    section_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    return get_attendance_by_date_and_class(date, class_id, section_id)


@router.get("/history/{student_id}")
def get_history(
    student_id: int,
    limit: int = 30,
    current_user: dict = Depends(get_current_user)
):
    return get_attendance_history(student_id, limit)


@router.get("/stats/{date}")
def get_stats(
    date: str,
    current_user: dict = Depends(get_current_user)
):
    return get_attendance_stats(date)