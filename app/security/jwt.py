from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import jwt

from app.core.config import settings

def create_access_token(subject: str) -> tuple[str, str]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "jti": jti,
        "type": "access",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti

def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "jti": jti,
        "type": "refresh",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire