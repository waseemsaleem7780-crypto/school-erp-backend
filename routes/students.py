from fastapi import APIRouter, Depends, HTTPException
from models.schemas import students
from services.student_service import (
    create_student,
    get_students_by_class,
    get_all_students,
    update_student,
    delete_student,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", status_code=201)
def add_student(
    student_data: students,
    current_user: dict = Depends(get_current_user)
):
    result = create_student(
        student_data.user_id,
        student_data.roll_number,
        student_data.class_id,
        student_data.section_id
    )
    return result


@router.get("/")
def get_all(
    current_user: dict = Depends(get_current_user)
):
    return get_all_students()


@router.get("/{class_id}")
def get_students(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_students_by_class(class_id)


@router.put("/{student_id}")
def edit_student(
    student_id: int,
    student_data: students,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit")
    
    result = update_student(
        student_id,
        student_data.roll_number,
        student_data.class_id,
        student_data.section_id
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return result


@router.delete("/{student_id}")
def remove_student(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")
    
    result = delete_student(student_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return result