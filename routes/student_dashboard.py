from fastapi import APIRouter, Depends, HTTPException
from services.student_dashboard_service import (
    get_student_stats,
    get_student_attendance,
    get_student_results,
    get_student_fees,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/student", tags=["Student Dashboard"])


@router.get("/my-stats")
def student_stats(current_user: dict = Depends(get_current_user)):
    """Student ke dashboard stats"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    return get_student_stats(current_user["user_id"])


@router.get("/my-attendance")
def student_attendance(current_user: dict = Depends(get_current_user)):
    """Student ki attendance"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    return get_student_attendance(current_user["user_id"])


@router.get("/my-results")
def student_results(current_user: dict = Depends(get_current_user)):
    """Student ke results"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    return get_student_results(current_user["user_id"])


@router.get("/my-fees")
def student_fees(current_user: dict = Depends(get_current_user)):
    """Student ki fees"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    return get_student_fees(current_user["user_id"])