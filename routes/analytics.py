from fastapi import APIRouter, Depends, HTTPException
from services.analytics_service import (
    get_attendance_trend,
    get_fee_collection,
    get_top_students,
    get_fee_defaulters,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/attendance-trend")
def attendance_trend(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access")
    return get_attendance_trend()


@router.get("/fee-collection")
def fee_collection(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access")
    return get_fee_collection()


@router.get("/top-students")
def top_students(limit: int = 10, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access")
    return get_top_students(limit)


@router.get("/defaulters")
def fee_defaulters(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access")
    return get_fee_defaulters()