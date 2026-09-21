import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

# ═══════════════════════════════════════════════════════════════
#  JWT SECRET ROTATION — Multiple secrets support
# ═══════════════════════════════════════════════════════════════
# Env vars mein multiple secrets rakho:
#   SECRET_KEY_CURRENT   → active key
#   SECRET_KEY_OLD_1     → previous key (grace period)
#   SECRET_KEY_OLD_2     → older key

def get_secrets():
    """Saari available secrets return karo — current + old."""
    secrets = []
    current = os.getenv("SECRET_KEY_CURRENT") or os.getenv("SECRET_KEY")
    if current:
        secrets.append(current)

    for i in range(1, 4):
        old = os.getenv(f"SECRET_KEY_OLD_{i}")
        if old:
            secrets.append(old)

    # Fallback — agar koi set nahi hai
    if not secrets:
        secrets.append("my_super_secret_key_123")
    return secrets


CURRENT_SECRET = get_secrets()[0]
ALL_SECRETS = get_secrets()
ALGORITHM = "HS256"

# Access token — chhota (15 min)
ACCESS_EXPIRY_MINUTES = 15
# Refresh token — lamba (7 days)
REFRESH_EXPIRY_DAYS = 7


# ═══════════════════════════════════════════════════════════════
#  CREATE TOKENS
# ═══════════════════════════════════════════════════════════════

def create_access_token(data: dict, expires_minutes: int = ACCESS_EXPIRY_MINUTES):
    """
    Access token banao — short lived.
    Data mein ye keys honi chahiye:
    - user_id
    - role
    - school_id
    - school_slug
    - institute_type
    """
    copy_data = data.copy()
    copy_data.update({
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "type": "access",
        "iat": datetime.utcnow(),
    })
    token = jwt.encode(copy_data, CURRENT_SECRET, algorithm=ALGORITHM)
    return token


def create_refresh_token(data: dict, expires_days: int = REFRESH_EXPIRY_DAYS):
    """Refresh token banao — long lived."""
    copy_data = data.copy()
    copy_data.update({
        "exp": datetime.utcnow() + timedelta(days=expires_days),
        "type": "refresh",
        "iat": datetime.utcnow(),
    })
    token = jwt.encode(copy_data, CURRENT_SECRET, algorithm=ALGORITHM)
    return token


# ═══════════════════════════════════════════════════════════════
#  DECODE TOKEN — Multiple secrets try karo
# ═══════════════════════════════════════════════════════════════

def decode_token(token: str):
    """
    Token decode karo — try all secrets (current + old).
    Agar koi secret match kare — valid.
    """
    for secret in ALL_SECRETS:
        try:
            payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            continue
    raise JWTError("Token verification failed with all secrets")


# Alias — purane code ke liye backward compatible
def decode_access_token(token: str):
    try:
        return decode_token(token)
    except JWTError:
        return None