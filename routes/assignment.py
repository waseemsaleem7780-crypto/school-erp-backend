from fastapi import APIRouter, Depends, HTTPException
from models.schemas import assignmentcreate
from services.assignment_service import create_assignment, get_assignments_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/assignment", tags=["Assignment"])


@router.post("/", status_code=201)
def add_assignment(
    assignment_data: assignmentcreate,
    current_user: dict = Depends(get_current_user),
):
    result = create_assignment(
        assignment_data.student_id,
        assignment_data.subject_id,
        assignment_data.teacher_id,
        assignment_data.title,
        assignment_data.description,
        str(assignment_data.deadline),
        getattr(assignment_data, "file_path", None),
    )
    return result


@router.get("/student/{student_id}")
def get_assignments(
    student_id: int,
    current_user: dict = Depends(get_current_user),
):
    return get_assignments_by_student(student_id)