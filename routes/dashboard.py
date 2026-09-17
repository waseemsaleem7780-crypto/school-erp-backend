from fastapi import APIRouter, Depends, HTTPException
from services.dashboard_service import get_dashboard_stats
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only admin can view dashboard")
    return get_dashboard_stats(school_id)