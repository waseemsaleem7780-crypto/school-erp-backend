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
    """
    Token nikaalo:
    1. HTTP-Only Cookie (preferred)
    2. Authorization Bearer header (fallback)
    """
    # ✅ Priority 1: Cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    # ✅ Priority 2: Authorization header
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
    """
    Token decode karo + DB se fresh user info lo.
    Role token se NAHI — DB se verify hota hai.
    """
    # 1. Token decode
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Access token check (refresh nahi)
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

    # 3. ✅ DB se fresh user info lo — role verify
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        """SELECT u.id, u.full_name, u.email, u.role, u.school_id,
                  u.is_active, u.deleted_at,
                  sch.subdomain AS school_slug,
                  COALESCE(sch.institute_type, 'school') AS institute_type
           FROM users u
           LEFT JOIN schools sch ON sch.id = u.school_id
           WHERE u.id = %s""",
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.get("deleted_at"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account deleted",
        )

    if user.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # ✅ Return fresh data — DB se
    return {
        "user_id": user["id"],
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],                    # ✅ DB se role
        "school_id": user["school_id"],
        "school_slug": user["school_slug"],
        "institute_type": user["institute_type"] or "school",
    }


# ═══════════════════════════════════════════════════════════════
#  SCHOOL ID HELPER
# ═══════════════════════════════════════════════════════════════

def get_current_school_id(current_user: dict = Depends(get_current_user)) -> int:
    """Current user ka school_id nikalo. Super admin ke liye None."""
    role = current_user.get("role")

    if role == "super_admin":
        return None

    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any school",
        )
    return school_id


# ═══════════════════════════════════════════════════════════════
#  ROLE GUARDS
# ═══════════════════════════════════════════════════════════════

def require_admin(current_user: dict = Depends(get_current_user)):
    """Sirf admin ya super_admin access kar sakta hai."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can access this",
        )
    return current_user


def require_super_admin(current_user: dict = Depends(get_current_user)):
    """Sirf super_admin access kar sakta hai."""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can access this",
        )
    return current_user


def require_teacher(current_user: dict = Depends(get_current_user)):
    """Sirf teacher access kar sakta hai."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teacher can access this",
        )
    return current_user


def require_student(current_user: dict = Depends(get_current_user)):
    """Sirf student access kar sakta hai."""
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only student can access this",
        )
    return current_user