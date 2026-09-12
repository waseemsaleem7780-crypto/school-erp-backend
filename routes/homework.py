from fastapi import APIRouter, Depends, HTTPException
from models.schemas import homeworkcreate
from services.homework_service import create_homework, get_homework_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/homework", tags=["Homework"])

@router.post("/", status_code=201)
def add_homework(
    hw_data: homeworkcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_homework(
        hw_data.student_id,
        hw_data.subject_id,
        hw_data.teacher_id,
        hw_data.title,
        hw_data.description,
        hw_data.deadline
    )
    return result

@router.get("/student/{student_id}")
def get_homework(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_homework_by_student(student_id)