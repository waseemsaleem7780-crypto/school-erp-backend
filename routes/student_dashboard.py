from fastapi import APIRouter, Depends, HTTPException
from services.student_dashboard_service import (   # ← service se import
    get_student_stats,
    get_student_attendance,
    get_student_results,
    get_student_fees,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/student/dashboard", tags=["Student Dashboard"])


@router.get("/stats")
def student_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_stats(current_user["id"])


@router.get("/attendance")
def student_attendance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_attendance(current_user["id"])


@router.get("/results")
def student_results(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_results(current_user["id"])


@router.get("/fees")
def student_fees(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_fees(current_user["id"])