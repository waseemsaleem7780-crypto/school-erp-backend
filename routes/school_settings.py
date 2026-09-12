from fastapi import APIRouter, Depends, HTTPException
from models.schemas import school_settingscreate
from services.school_settings_service import create_setting, get_all_settings, get_setting_by_key
from utils.dependencies import get_current_user

router = APIRouter(prefix="/school-settings", tags=["School Settings"])

@router.post("/", status_code=201)
def add_setting(
    setting_data: school_settingscreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_setting(
        setting_data.setting_key,
        setting_data.setting_value
    )
    return result

@router.get("/")
def get_settings(
    current_user: dict = Depends(get_current_user)
):
    return get_all_settings()

@router.get("/{setting_key}")
def get_setting(
    setting_key: str,
    current_user: dict = Depends(get_current_user)
):
    result = get_setting_by_key(setting_key)
    if not result:
        raise HTTPException(status_code=404, detail="Setting not found")
    return result