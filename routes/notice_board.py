from fastapi import APIRouter, Depends, HTTPException
from models.schemas import notice_boardcreate
from services.notice_board_service import create_notice, get_notices_by_class
from utils.dependencies import get_current_user

router = APIRouter(prefix="/notice-board", tags=["Notice Board"])

@router.post("/", status_code=201)
def add_notice(
    notice_data: notice_boardcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_notice(
        notice_data.title,
        notice_data.context,
        notice_data.class_id,
        notice_data.section_id,
        notice_data.posted_by,
        notice_data.target_audience_id,
        notice_data.is_active
    )
    return result

@router.get("/class/{class_id}")
def get_notices(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_notices_by_class(class_id)