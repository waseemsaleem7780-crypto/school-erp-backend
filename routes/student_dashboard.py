from fastapi import APIRouter, Depends, HTTPException
from services.student_dashboard_service import (
    get_student_stats,
    get_student_attendance,
    get_student_results,
    get_student_fees,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/student/dashboard", tags=["Student Dashboard"])


def get_user_id(current_user: dict) -> int:
    """Safe helper — id ya user_id dono handle karta hai."""
    return current_user.get("id") or current_user.get("user_id")


@router.get("/stats")
def student_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_stats(get_user_id(current_user))


@router.get("/attendance")
def student_attendance(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_attendance(get_user_id(current_user))


@router.get("/results")
def student_results(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_results(get_user_id(current_user))


@router.get("/fees")
def student_fees(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_fees(get_user_id(current_user))