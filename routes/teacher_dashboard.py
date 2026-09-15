from fastapi import APIRouter, Depends, HTTPException
from services.teacher_dashboard_service import (
    get_teacher_stats,
    get_teacher_classes,
    get_teacher_students,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/teacher", tags=["Teacher Dashboard"])


@router.get("/my-stats")
def teacher_stats(current_user: dict = Depends(get_current_user)):
    """Teacher ke dashboard stats"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    
    return get_teacher_stats(current_user["user_id"])


@router.get("/my-classes")
def teacher_classes(current_user: dict = Depends(get_current_user)):
    """Teacher ki classes"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    
    return get_teacher_classes(current_user["user_id"])


@router.get("/my-students/{class_id}")
def teacher_students(class_id: int, current_user: dict = Depends(get_current_user)):
    """Class ke students"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    
    return get_teacher_students(class_id)