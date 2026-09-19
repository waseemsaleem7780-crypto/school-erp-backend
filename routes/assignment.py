from fastapi import APIRouter, Depends, HTTPException
from models.schemas import assignmentcreate
from services.assignment_service import (
    create_assignment,
    get_all_assignments,
    get_assignments_by_student,
    update_assignment,
    delete_assignment,
)
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/assignment", tags=["Assignment"])


@router.post("/", status_code=201)
def add_assignment(
    assignment_data: assignmentcreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Assignment banao — sirf is school ke student ke liye."""
    result = create_assignment(
        assignment_data.student_id,
        assignment_data.subject_id,
        assignment_data.teacher_id,
        assignment_data.title,
        assignment_data.description,
        str(assignment_data.deadline),
        getattr(assignment_data, "file_path", None),
        school_id
    )
    return result


@router.get("/")
def get_all(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Sirf is school ki assignments."""
    return get_all_assignments(school_id)


@router.get("/student/{student_id}")
def get_assignments(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Ek student ki assignments — sirf is school ka."""
    return get_assignments_by_student(student_id, school_id)


@router.put("/{assignment_id}")
def edit_assignment(
    assignment_id: int,
    assignment_data: assignmentcreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only teachers can edit")
    
    result = update_assignment(
        assignment_id,
        assignment_data.title,
        assignment_data.description,
        str(assignment_data.deadline),
        getattr(assignment_data, "file_path", None),
        school_id
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return result


@router.delete("/{assignment_id}")
def remove_assignment(
    assignment_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only teachers can delete")
    
    result = delete_assignment(assignment_id, school_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return result