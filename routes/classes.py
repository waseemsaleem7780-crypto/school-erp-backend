from fastapi import APIRouter, Depends, HTTPException
from models.schemas import classescreate
from services.class_service import create_class, get_all_classes
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