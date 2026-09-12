from fastapi import APIRouter, Depends, HTTPException
from models.schemas import teacherscreate
from services.teacher_service import create_teacher, get_all_teachers
from utils.dependencies import get_current_user

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("/", status_code=201)
def add_teacher(
    teacher_data: teacherscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_teacher(teacher_data.user_id, teacher_data.qualification)
    return result

@router.get("/")
def get_teachers(
    current_user: dict = Depends(get_current_user)
):
    return get_all_teachers()