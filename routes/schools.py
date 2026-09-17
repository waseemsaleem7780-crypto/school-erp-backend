from fastapi import APIRouter, Depends, HTTPException
from models.schemas import schoolscreate
from services.school_service import (
    create_school,
    get_all_schools,
    get_school_by_id,
    update_school,
    delete_school,
    get_school_stats,
)
from utils.dependencies import get_current_user, require_super_admin

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post("/", status_code=201)
def add_school(
    school_data: schoolscreate,
    current_user: dict = Depends(require_super_admin)
):
    """Sirf super admin naya school add kar sakta hai."""
    return create_school(
        school_data.name,
        school_data.subdomain,
        school_data.admin_email,
        school_data.phone,
        school_data.address
    )


@router.get("/")
def get_schools(current_user: dict = Depends(require_super_admin)):
    """Sirf super admin saare schools dekh sakta hai."""
    return get_all_schools()


@router.get("/stats")
def school_stats(current_user: dict = Depends(require_super_admin)):
    """Overall stats — total schools, admins, students."""
    return get_school_stats()


@router.get("/{school_id}")
def get_school(
    school_id: int,
    current_user: dict = Depends(require_super_admin)
):
    result = get_school_by_id(school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result


@router.put("/{school_id}")
def edit_school(
    school_id: int,
    school_data: schoolscreate,
    current_user: dict = Depends(require_super_admin)
):
    result = update_school(
        school_id,
        school_data.name,
        school_data.subdomain,
        school_data.admin_email,
        school_data.phone,
        school_data.address
    )
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result


@router.delete("/{school_id}")
def remove_school(
    school_id: int,
    current_user: dict = Depends(require_super_admin)
):
    result = delete_school(school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result