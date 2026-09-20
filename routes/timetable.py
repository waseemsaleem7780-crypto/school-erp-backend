from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from services.timetable_service import create_timetable, get_timetable_by_class
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/timetable", tags=["Timetable"])


class TimetableCreateMultiple(BaseModel):
    class_id: int
    section_id: int
    subject_id: int
    teacher_id: int
    days: List[str]
    start_time: str
    end_time: str


@router.post("/", status_code=201)
def add_timetable(
    timetable_data: TimetableCreateMultiple,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Multiple days ke liye timetable entry banao."""
    if not timetable_data.days:
        raise HTTPException(status_code=400, detail="Kam se kam ek din select karo")

    results = []
    for day in timetable_data.days:
        result = create_timetable(
            timetable_data.class_id,
            timetable_data.section_id,
            timetable_data.subject_id,
            timetable_data.teacher_id,
            day,
            timetable_data.start_time,
            timetable_data.end_time
        )
        results.append(result)

    return {
        "message": f"Timetable entry added for {len(results)} day(s)",
        "entries": results
    }


@router.get("/class/{class_id}")
def get_timetable(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Class ki timetable — subject aur teacher ke naam ke saath."""
    return get_timetable_by_class(class_id)