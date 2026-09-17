from fastapi import APIRouter, Depends, HTTPException
from models.schemas import classescreate
from services.class_service import (
    create_class,
    get_all_classes,
    update_class,
    delete_class,
    restore_class,
)
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.post("/", status_code=201)
def add_class(
    class_data: classescreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    result = create_class(class_data.name, school_id)
    return result


@router.get("/")
def get_classes(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    return get_all_classes(school_id)


@router.put("/{class_id}")
def edit_class(
    class_id: int,
    class_data: classescreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can edit")

    result = update_class(class_id, class_data.name, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Class not found")

    return result


@router.delete("/{class_id}")
def remove_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Soft delete."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_class(class_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Class not found")

    return result


@router.post("/{class_id}/restore")
def restore_deleted_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Soft-deleted class ko restore karo."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can restore")

    result = restore_class(class_id, school_id)

    if not result:
        raise HTTPException(status_code=404, detail="Class not found or not deleted")

    return result