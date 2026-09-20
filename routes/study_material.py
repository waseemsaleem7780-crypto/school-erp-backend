from fastapi import APIRouter, Depends
from models.schemas import study_materialcreate
from services.study_material_service import create_study_material, get_study_material_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/study-material", tags=["Study Material"])


@router.post("/", status_code=201)
def add_study_material(
    material_data: study_materialcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_study_material(
        material_data.class_id,
        material_data.subject_id,
        material_data.section_id,
        material_data.teacher_id,
        material_data.title,
        material_data.description,
        material_data.file_path
    )
    return result


@router.get("/class/{class_id}")
def get_study_material(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_study_material_by_class(class_id)