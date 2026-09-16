from fastapi import APIRouter, Depends, HTTPException
from models.schemas import classescreate
from services.class_service import (
    create_class,
    get_all_classes,
    update_class,
    delete_class,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.post("/", status_code=201)
def add_class(
    class_data: classescreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_class(class_data.name)
    return result


@router.get("/")
def get_classes(
    current_user: dict = Depends(get_current_user)
):
    return get_all_classes()


@router.put("/{class_id}")
def edit_class(
    class_id: int,
    class_data: classescreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit")

    result = update_class(class_id, class_data.name)

    if not result:
        raise HTTPException(status_code=404, detail="Class not found")

    return result


@router.delete("/{class_id}")
def remove_class(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    result = delete_class(class_id)

    if not result:
        raise HTTPException(status_code=404, detail="Class not found")

    return result