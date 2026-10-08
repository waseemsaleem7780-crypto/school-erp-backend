from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.schemas import guardianscreate
from services.guardians_service import (
    create_guardian,
    create_guardian_auto,
    get_guardians_by_student,
)
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/guardians", tags=["Guardians"])


class GuardianAutoCreate(BaseModel):
    student_id: int
    full_name: str
    relation: str
    phone_number: str
    email: str
    address: str


@router.post("/", status_code=201)
def add_guardian(
    guardian_data: guardianscreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    result = create_guardian(
        guardian_data.user_id,
        guardian_data.student_id,
        guardian_data.full_name,
        guardian_data.relation,
        guardian_data.phone_number,
        guardian_data.email,
        guardian_data.address,
        school_id=school_id,
    )
    return result


@router.post("/auto", status_code=201)
def add_guardian_auto(
    data: GuardianAutoCreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    result = create_guardian_auto(
        student_id=data.student_id,
        full_name=data.full_name,
        relation=data.relation,
        phone_number=data.phone_number,
        email=data.email,
        address=data.address,
        school_id=school_id,
    )
    return result


@router.get("/student/{student_id}")
def get_guardians(
    student_id: int,
    current_user: dict = Depends(get_current_user),
):
    return get_guardians_by_student(student_id)
