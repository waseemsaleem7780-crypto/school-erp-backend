from fastapi import APIRouter, HTTPException
from models.schemas import usercreate, userlogin
from services.auth_service import hash_password, verify_password, get_user_by_email, create_new_user
from utils.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=201)
def register_user(user_data: usercreate):
    result = create_new_user(user_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/login")
def login_user(login_data: userlogin):
    user = get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    is_valid = verify_password(login_data.password, user["password"])  # ✅ password (not password_hash)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}