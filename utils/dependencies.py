from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import decode_access_token

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_school_id(current_user: dict = Depends(get_current_user)) -> int:
    """Current user ka school_id nikalo. Super admin ke liye None."""
    role = current_user.get("role")

    # Super admin ke paas school_id nahi hota
    if role == "super_admin":
        return None

    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any school",
        )
    return school_id


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