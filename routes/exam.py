from fastapi import APIRouter, Depends, HTTPException
from models.schemas import examcreate
from services.exam_service import create_exam, get_exams_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/exam", tags=["Exam"])

@router.post("/", status_code=201)
def add_exam(
    exam_data: examcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_exam(
        exam_data.name,
        exam_data.class_id,
        exam_data.subject_id,
        exam_data.exam_date,
        exam_data.total_marks,
        exam_data.passing_marks
    )
    return result

@router.get("/class/{class_id}")
def get_exams(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_exams_by_class(class_id)