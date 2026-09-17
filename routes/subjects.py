from fastapi import APIRouter, Depends, HTTPException
from models.schemas import subjectscreate
from services.subject_service import (
    create_subject,
    get_all_subjects,
    get_subjects_by_class,
    update_subject,
    delete_subject,
    restore_subject,
)
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", status_code=201)
def add_subject(
    subject_data: subjectscreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    teacher_id = getattr(subject_data, "teacher_id", None)
    return create_subject(
        subject_data.name,
        subject_data.code,
        subject_data.class_id,
        teacher_id,
        school_id
    )


@router.get("/")
def get_subjects(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_all_subjects(school_id)


@router.get("/class/{class_id}")
def get_subjects_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_subjects_by_class(class_id, school_id)


@router.put("/{subject_id}")
def edit_subject(
    subject_id: int,
    subject_data: subjectscreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can edit")

    teacher_id = getattr(subject_data, "teacher_id", None)
    result = update_subject(
        subject_id,
        subject_data.name,
        subject_data.code,
        subject_data.class_id,
        teacher_id,
        school_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")
    return result


@router.delete("/{subject_id}")
def remove_subject(
    subject_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Soft delete."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_subject(subject_id, school_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subject not found")
    return result


@router.post("/{subject_id}/restore")
def restore_deleted_subject(
    subject_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Soft-deleted subject ko restore karo."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can restore")

    result = restore_subject(subject_id, school_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subject not found or not deleted")
    return result