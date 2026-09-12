from fastapi import APIRouter, Depends, HTTPException
from models.schemas import fee_paymentcreate
from services.fee_payment_service import create_fee_payment, get_fee_payments_by_student
from utils.dependencies import get_current_user

router = APIRouter(prefix="/fee-payment", tags=["Fee Payment"])

@router.post("/", status_code=201)
def add_fee_payment(
    fee_data: fee_paymentcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_fee_payment(
        fee_data.student_id,
        fee_data.monthly_fee,
        fee_data.yearly_fee,
        fee_data.amount,
        fee_data.payment_mod
    )
    return result

@router.get("/student/{student_id}")
def get_fee_payments(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_fee_payments_by_student(student_id)