from fastapi import APIRouter, Depends, HTTPException
from models.schemas import resultcreate
from services.results_service import create_result, get_results_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/results", tags=["Results"])

@router.post("/", status_code=201)
def add_result(
    result_data: resultcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_result(
        result_data.exam_id,
        result_data.student_id,
        result_data.subject_id,
        result_data.marks_obtained,
        result_data.grade,
        result_data.remarks
    )
    return result

@router.get("/student/{student_id}")
def get_results(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_results_by_student(student_id)