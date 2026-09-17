from fastapi import APIRouter, Depends, HTTPException
from services.teacher_dashboard_service import (
    get_teacher_stats,
    get_teacher_classes,
    get_teacher_students,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/teacher", tags=["Teacher Dashboard"])


def get_user_id(current_user: dict) -> int:
    """Safe helper — id ya user_id dono handle karta hai."""
    return current_user.get("id") or current_user.get("user_id")


@router.get("/my-stats")
def teacher_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    return get_teacher_stats(get_user_id(current_user))


@router.get("/my-classes")
def teacher_classes(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    return get_teacher_classes(get_user_id(current_user))


@router.get("/my-students/{class_id}")
def teacher_students(class_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this")
    return get_teacher_students(class_id)