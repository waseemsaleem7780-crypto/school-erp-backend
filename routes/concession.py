from fastapi import APIRouter, Depends, HTTPException
from models.schemas import concessioncreate
from services.concession_service import create_concession, get_concessions_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/concession", tags=["Concession"])

@router.post("/", status_code=201)
def add_concession(
    concession_data: concessioncreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_concession(
        concession_data.student_id,
        concession_data.user_id,
        concession_data.academic_year_id,
        concession_data.concession_type,
        concession_data.concession_value,
        concession_data.reason
    )
    return result

@router.get("/student/{student_id}")
def get_concessions(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_concessions_by_student(student_id)