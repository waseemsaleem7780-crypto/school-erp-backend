from fastapi import APIRouter, Depends
from services.dashboard_service import get_dashboard_stats
from utils.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def dashboard_stats(current_user: dict = Depends(get_current_user)):
    return get_dashboard_stats()