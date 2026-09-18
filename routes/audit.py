from fastapi import APIRouter, Depends
from services.audit_service import get_audit_logs
from utils.dependencies import require_super_admin

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/")
def list_logs(
    limit: int = 100,
    current_user: dict = Depends(require_super_admin)
):
    """Sirf super admin audit logs dekh sakta hai."""
    return get_audit_logs(limit=limit)
