from fastapi import APIRouter, Depends, HTTPException
from models.schemas import timetablecreate
from services.timetable_service import create_timetable, get_timetable_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/timetable", tags=["Timetable"])

@router.post("/", status_code=201)
def add_timetable(
    timetable_data: timetablecreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_timetable(
        timetable_data.class_id,
        timetable_data.section_id,
        timetable_data.subject_id,
        timetable_data.teacher_id,
        timetable_data.day_of_week,
        timetable_data.start_time,
        timetable_data.end_time
    )
    return result

@router.get("/class/{class_id}")
def get_timetable(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_timetable_by_class(class_id)