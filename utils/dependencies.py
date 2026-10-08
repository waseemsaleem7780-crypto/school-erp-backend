from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import decode_token
from database.db import get_db_connection, get_dict_cursor

# ⚠️ auto_error=False — kyunki cookie se bhi token aa sakta hai
security = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════
#  TOKEN EXTRACTION — Cookie ya Header dono se
# ═══════════════════════════════════════════════════════════════

def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Token nikaalo: cookie ya header se."""
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    if credentials and credentials.credentials:
        return credentials.credentials

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ═══════════════════════════════════════════════════════════════
#  GET CURRENT USER — DB se role verify
# ═══════════════════════════════════════════════════════════════

def get_current_user(token: str = Depends(extract_token)):
    """Token decode + DB se fresh user info."""
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # ✅ Simple query — single-school setup
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, full_name, email, role FROM users WHERE id = %s",
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "user_id": user["id"],
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "school_id": 1,  # single-school — default 1
        "school_slug": "default",
        "institute_type": "school",
    }


# ═══════════════════════════════════════════════════════════════
#  SCHOOL ID HELPER — single school
# ═══════════════════════════════════════════════════════════════

def get_current_school_id(current_user: dict = Depends(get_current_user)) -> int:
    """Current user ka school_id. Single-school setup mein 1 return karo."""
    return 1


# ═══════════════════════════════════════════════════════════════
#  ROLE GUARDS
# ═══════════════════════════════════════════════════════════════

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access this",
        )
    return current_user


def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can access this",
        )
    return current_user


def require_teacher(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teacher can access this",
        )
    return current_user


def require_student(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only student can access this",
        )
    return current_user
