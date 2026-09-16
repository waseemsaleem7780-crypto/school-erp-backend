from fastapi import APIRouter, Depends, HTTPException
from models.schemas import teacherscreate
from services.teacher_service import (
    create_teacher,
    get_all_teachers,
    update_teacher,
    delete_teacher,
)
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


@router.put("/{teacher_id}")
def edit_teacher(
    teacher_id: int,
    teacher_data: teacherscreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit")
    
    result = update_teacher(teacher_id, teacher_data.qualification)
    
    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return result


@router.delete("/{teacher_id}")
def remove_teacher(
    teacher_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")
    
    result = delete_teacher(teacher_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return result