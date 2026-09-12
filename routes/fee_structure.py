from fastapi import APIRouter, Depends, HTTPException
from models.schemas import fee_structurecreate
from services.fee_structure_service import create_fee_structure, get_fee_structure_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/fee-structure", tags=["Fee Structure"])

@router.post("/", status_code=201)
def add_fee_structure(
    fee_data: fee_structurecreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_fee_structure(
        fee_data.class_id,
        fee_data.month,
        fee_data.yearly_fee,
        fee_data.amount,
        fee_data.due_date
    )
    return result

@router.get("/class/{class_id}")
def get_fee_structure(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_fee_structure_by_class(class_id)