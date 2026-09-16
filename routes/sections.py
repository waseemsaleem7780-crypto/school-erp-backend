from fastapi import APIRouter, Depends, HTTPException
from models.schemas import sectionscreate
from services.section_service import (
    create_section,
    get_sections_by_class,
    get_all_sections,
    update_section,
    delete_section,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.post("/", status_code=201)
def add_section(
    section_data: sectionscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_section(section_data.name, section_data.class_id)
    return result


@router.get("/")
def get_all(
    current_user: dict = Depends(get_current_user)
):
    return get_all_sections()


@router.get("/{class_id}")
def get_sections(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_sections_by_class(class_id)


@router.put("/{section_id}")
def edit_section(
    section_id: int,
    section_data: sectionscreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit")
    
    result = update_section(section_id, section_data.name, section_data.class_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return result


@router.delete("/{section_id}")
def remove_section(
    section_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")
    
    result = delete_section(section_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return result