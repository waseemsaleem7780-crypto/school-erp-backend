from fastapi import APIRouter, Depends, HTTPException
from models.schemas import guardianscreate  # aapki schemas.py mein class guardianscreate hai
from services.guardians_service import create_guardian, get_guardians_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/guardians", tags=["Guardians"])

@router.post("/", status_code=201)
def add_guardian(
    guardian_data: guardianscreate,
    current_user: dict = Depends(get_current_user)
):
    # Service call karo (7 values)
    result = create_guardian(
        guardian_data.user_id,
        guardian_data.student_id,
        guardian_data.full_name,
        guardian_data.relation,
        guardian_data.phone_number,
        guardian_data.email,
        guardian_data.address
    )
    return result
@router.get("/student/{student_id}")
def get_guardians(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_guardians_by_student(student_id)