from fastapi import APIRouter, Depends, HTTPException
from models.schemas import academic_yearscreate
from services.academic_years_service import create_academic_year, get_all_academic_years
from utils.dependencies import get_current_user

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])

@router.post("/", status_code=201)
def add_academic_year(
    year_data: academic_yearscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_academic_year(
        year_data.year,
        year_data.start_date,
        year_data.end_date
    )
    return result

@router.get("/")
def get_academic_years(
    current_user: dict = Depends(get_current_user)
):
    return get_all_academic_years() 