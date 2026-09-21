from fastapi import APIRouter, HTTPException, Request, Response, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta

from models.schemas import usercreate, userlogin
from services.auth_service import (
    hash_password,
    verify_password,
    get_user_by_email,
    create_new_user,
)
from services.audit_service import log_action
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from utils.dependencies import get_current_user
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ═══════════════════════════════════════════════════════════════
#  COOKIE HELPERS — Cross-Domain Support
# ═══════════════════════════════════════════════════════════════

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    HTTP-Only cookies set karo.
    ✅ samesite="none" — cross-domain (Vercel → Railway) ke liye ZAROORI
    ✅ secure=True — HTTPS mandatory
    """
    # Access token — 15 minutes
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,       # JavaScript access nahi
        secure=True,         # HTTPS only
        samesite="none",     # ✅ CRITICAL — cross-domain
        max_age=15 * 60,
        path="/",
    )
    # Refresh token — 7 days
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",     # ✅ CRITICAL
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookies(response: Response):
    """Logout par cookies clear karo."""
    response.delete_cookie(
        key="access_token", path="/",
        samesite="none", secure=True,
    )
    response.delete_cookie(
        key="refresh_token", path="/",
        samesite="none", secure=True,
    )


# ============ REGISTER ============
@router.post("/register", status_code=201)
def register_user(user_data: usercreate):
    result = create_new_user(user_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ LOGIN ============
@router.post("/login")
@limiter.limit("5/minute")
def login_user(request: Request, response: Response, login_data: userlogin):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        user = get_user_by_email(login_data.email)

        if not user:
            log_action(
                user_id=None, school_id=None, action="LOGIN_FAILED",
                details={"email": login_data.email, "reason": "user_not_found"},
                ip=request.client.host,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if user.get("locked_until") and user["locked_until"] > datetime.now():
            remaining = int((user["locked_until"] - datetime.now()).total_seconds() // 60)
            log_action(
                user_id=user["id"], school_id=user.get("school_id"),
                action="LOGIN_BLOCKED",
                details={"email": user["email"], "reason": "account_locked"},
                ip=request.client.host,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=403, detail=f"Account locked. Try again in {remaining} minutes.")

        is_valid = verify_password(login_data.password, user["password"])

        if not is_valid:
            new_attempts = (user.get("failed_attempts") or 0) + 1

            if new_attempts >= 5:
                lock_until = datetime.now() + timedelta(minutes=15)
                cursor.execute(
                    "UPDATE users SET failed_attempts = %s, locked_until = %s WHERE id = %s",
                    (new_attempts, lock_until, user["id"]),
                )
                conn.commit()
                log_action(
                    user_id=user["id"], school_id=user.get("school_id"),
                    action="ACCOUNT_LOCKED",
                    details={"email": user["email"], "attempts": new_attempts},
                    ip=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(status_code=403, detail="Account locked for 15 minutes. Too many failed attempts.")
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts = %s WHERE id = %s",
                    (new_attempts, user["id"]),
                )
                conn.commit()
                log_action(
                    user_id=user["id"], school_id=user.get("school_id"),
                    action="LOGIN_FAILED",
                    details={"email": user["email"], "attempts": new_attempts},
                    ip=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(status_code=401, detail=f"Invalid password. {5 - new_attempts} attempts left.")

        # ✅ Success
        cursor.execute(
            """UPDATE users 
               SET failed_attempts = 0, 
                   locked_until = NULL, 
                   last_login = CURRENT_TIMESTAMP, 
                   login_count = COALESCE(login_count, 0) + 1 
               WHERE id = %s""",
            (user["id"],),
        )
        conn.commit()

        # School slug + institute_type
        school_slug = None
        institute_type = "school"
        if user.get("school_id"):
            cursor.execute(
                "SELECT subdomain, COALESCE(institute_type, 'school') as institute_type FROM schools WHERE id = %s",
                (user["school_id"],),
            )
            school = cursor.fetchone()
            if school:
                school_slug = school["subdomain"]
                institute_type = school["institute_type"] or "school"

        log_action(
            user_id=user["id"], school_id=user.get("school_id"),
            action="LOGIN_SUCCESS",
            details={"email": user["email"], "role": user["role"]},
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )

        # Token payload
        token_payload = {
            "user_id": user["id"],
            "role": user["role"],
            "school_id": user.get("school_id"),
            "school_slug": school_slug,
            "institute_type": institute_type,
        }

        # ✅ Access + Refresh tokens banao
        access_token = create_access_token(token_payload, expires_minutes=15)
        refresh_token = create_refresh_token(token_payload, expires_days=7)

        # ✅ HTTP-Only Cookies set karo (SameSite=None)
        set_auth_cookies(response, access_token, refresh_token)

        # Token response mein NAHI — sirf user info
        return {
            "success": True,
            "role": user["role"],
            "school_slug": school_slug,
            "institute_type": institute_type,
            "user_name": user.get("full_name"),
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ============ REFRESH TOKEN ============
@router.post("/refresh")
def refresh_access_token(request: Request, response: Response):
    """Refresh token se naya access token lo."""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # ✅ Naya access token banao
        token_payload = {
            "user_id": payload["user_id"],
            "role": payload.get("role"),
            "school_id": payload.get("school_id"),
            "school_slug": payload.get("school_slug"),
            "institute_type": payload.get("institute_type"),
        }
        new_access_token = create_access_token(token_payload, expires_minutes=15)

        # ✅ SameSite=None ke saath cookie update karo
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",     # ✅ CRITICAL
            max_age=15 * 60,
            path="/",
        )

        return {"success": True, "message": "Token refreshed"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")


# ============ LOGOUT ============
@router.post("/logout")
def logout_user(response: Response):
    """Cookies clear karo."""
    clear_auth_cookies(response)
    return {"success": True, "message": "Logged out"}


# ============ GET CURRENT USER ============
@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Current logged-in user ka data."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    user_id = current_user.get("user_id") or current_user.get("id")

    cursor.execute(
        """SELECT 
               u.id, u.full_name, u.email, u.role, u.school_id,
               s.id as student_id, s.roll_number, s.class_id, s.section_id,
               t.id as teacher_id, t.qualification,
               sch.name as school_name,
               sch.subdomain as school_slug,
               COALESCE(sch.institute_type, 'school') as institute_type
           FROM users u
           LEFT JOIN students s ON s.user_id = u.id AND s.deleted_at IS NULL
           LEFT JOIN teachers t ON t.user_id = u.id AND t.deleted_at IS NULL
           LEFT JOIN schools sch ON sch.id = u.school_id
           WHERE u.id = %s AND u.deleted_at IS NULL""",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(user)


# ============ UNLOCK ACCOUNT (Super Admin) ============
@router.post("/unlock/{user_id}")
def unlock_account(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        cursor.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s RETURNING id",
            (user_id,),
        )
        result = cursor.fetchone()
        conn.commit()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Account unlocked", "user_id": user_id}
    finally:
        conn.close()