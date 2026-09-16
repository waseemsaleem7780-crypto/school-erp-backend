from fastapi import APIRouter, Depends, HTTPException
from models.schemas import subjectscreate
from services.subject_service import (
    create_subject,
    get_all_subjects,
    get_subjects_by_class,
    update_subject,
    delete_subject,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", status_code=201)
def add_subject(
    subject_data: subjectscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_subject(
        subject_data.name,
        subject_data.class_id,
        getattr(subject_data, "teacher_id", None)
    )
    return result


@router.get("/")
def get_subjects(
    current_user: dict = Depends(get_current_user)
):
    return get_all_subjects()


@router.get("/class/{class_id}")
def get_subjects_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_subjects_by_class(class_id)


@router.put("/{subject_id}")
def edit_subject(
    subject_id: int,
    subject_data: subjectscreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit")

    result = update_subject(
        subject_id,
        subject_data.name,
        subject_data.class_id,
        getattr(subject_data, "teacher_id", None)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")

    return result


@router.delete("/{subject_id}")
def remove_subject(
    subject_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_subject(subject_id)

    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")

    return result