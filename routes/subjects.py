from fastapi import APIRouter, Depends, HTTPException
from models.schemas import subjectscreate
from services.subject_service import create_subject, get_subjects_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.post("/", status_code=201)
def add_subject(
    subject_data: subjectscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_subject(subject_data.name, subject_data.code, subject_data.class_id)
    return result

@router.get("/{class_id}")
def get_subjects(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_subjects_by_class(class_id)