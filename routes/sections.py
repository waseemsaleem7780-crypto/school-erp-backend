from fastapi import APIRouter, Depends, HTTPException
from models.schemas import sectionscreate
from services.section_service import create_section, get_sections_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/sections", tags=["Sections"])

@router.post("/", status_code=201)
def add_section(
    section_data: sectionscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_section(section_data.name, section_data.class_id)  
    return result

@router.get("/{class_id}")
def get_sections(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_sections_by_class(class_id)