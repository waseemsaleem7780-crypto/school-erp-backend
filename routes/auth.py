from fastapi import APIRouter, HTTPException, Request, Depends
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
from utils.jwt_handler import create_access_token
from utils.dependencies import get_current_user
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


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
def login_user(request: Request, login_data: userlogin):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # 1. User dhundo
        user = get_user_by_email(login_data.email)

        if not user:
            log_action(
                user_id=None,
                school_id=None,
                action="LOGIN_FAILED",
                details={"email": login_data.email, "reason": "user_not_found"},
                ip=request.client.host,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # 2. Account locked hai?
        if user.get("locked_until") and user["locked_until"] > datetime.now():
            remaining = int((user["locked_until"] - datetime.now()).total_seconds() // 60)
            log_action(
                user_id=user["id"],
                school_id=user.get("school_id"),
                action="LOGIN_BLOCKED",
                details={"email": user["email"], "reason": "account_locked"},
                ip=request.client.host,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(
                status_code=403,
                detail=f"Account locked. Try again in {remaining} minutes.",
            )

        # 3. Password verify
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
                    user_id=user["id"],
                    school_id=user.get("school_id"),
                    action="ACCOUNT_LOCKED",
                    details={"email": user["email"], "attempts": new_attempts},
                    ip=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(
                    status_code=403,
                    detail="Account locked for 15 minutes. Too many failed attempts.",
                )
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts = %s WHERE id = %s",
                    (new_attempts, user["id"]),
                )
                conn.commit()

                log_action(
                    user_id=user["id"],
                    school_id=user.get("school_id"),
                    action="LOGIN_FAILED",
                    details={"email": user["email"], "attempts": new_attempts},
                    ip=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                )
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid password. {5 - new_attempts} attempts left.",
                )

        # 4. Sahi password — reset attempts + update login info
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

        # 5. School slug + institute_type dhundo
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

        # 6. Audit log — success
        log_action(
            user_id=user["id"],
            school_id=user.get("school_id"),
            action="LOGIN_SUCCESS",
            details={"email": user["email"], "role": user["role"]},
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )

        # 7. Token payload
        token_payload = {
            "user_id": user["id"],
            "role": user["role"],
        }
        if user.get("school_id"):
            token_payload["school_id"] = user["school_id"]
        if school_slug:
            token_payload["school_slug"] = school_slug
        if institute_type:
            token_payload["institute_type"] = institute_type

        token = create_access_token(token_payload)

        return {
            "access_token": token,
            "token_type": "bearer",
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


# ============ GET CURRENT USER ============
@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user)
):
    """
    Current logged-in user ka data.
    - Student ke liye: student_id, roll_number, class_id, section_id
    - Teacher ke liye: teacher_id, qualification
    - Sabke liye: institute_type
    """
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
    """Super admin kisi bhi user ka account unlock kar sakta hai."""
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