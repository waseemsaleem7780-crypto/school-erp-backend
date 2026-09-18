from fastapi import APIRouter, HTTPException
from models.schemas import usercreate, userlogin
from services.auth_service import hash_password, verify_password, get_user_by_email, create_new_user
from utils.jwt_handler import create_access_token
from database.db import get_db_connection, get_dict_cursor

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

    is_valid = verify_password(login_data.password, user["password"])
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """UPDATE users 
           SET last_login = CURRENT_TIMESTAMP, 
               login_count = COALESCE(login_count, 0) + 1 
           WHERE id = %s""",
        (user["id"],)
    )
    conn.commit()

    # ✅ School slug dhundo
    school_slug = None
    if user.get("school_id"):
        cursor.execute(
            "SELECT subdomain FROM schools WHERE id = %s",
            (user["school_id"],)
        )
        school = cursor.fetchone()
        if school:
            school_slug = school["subdomain"]
    conn.close()

    # Token payload
    token_payload = {
        "user_id": user["id"],
        "role": user["role"],
    }
    if user.get("school_id"):
        token_payload["school_id"] = user["school_id"]
    if school_slug:
        token_payload["school_slug"] = school_slug

    token = create_access_token(token_payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "school_slug": school_slug,
        "user_name": user.get("full_name"),
    }