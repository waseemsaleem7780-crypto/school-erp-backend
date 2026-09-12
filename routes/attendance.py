from fastapi import APIRouter, Depends, HTTPException
from models.schemas import attendancecreate
from services.attendance_service import create_attendance, get_attendance_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/", status_code=201)
def add_attendance(
    att_data: attendancecreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_attendance(
        att_data.student_id,
        att_data.date,
        att_data.status,
        att_data.marked_by
    )
    return result

@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_attendance_by_student(student_id)