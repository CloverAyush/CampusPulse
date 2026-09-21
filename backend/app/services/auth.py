import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
import jwt

from app.config import settings

logger = logging.getLogger(__name__)

BCRYPT_MAX_PASSWORD_BYTES = 72


def _encode(password: str) -> bytes:
    """bcrypt silently truncates past 72 bytes, which would make two different long
    passwords interchangeable. Reject rather than truncate."""
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Password may not exceed {BCRYPT_MAX_PASSWORD_BYTES} bytes")
    return encoded


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + delta

    payload = {"exp": expire, "iat": now, "nbf": now, "sub": str(subject), "role": role}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, int(delta.total_seconds())


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        logger.info("Rejected expired token")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("Rejected invalid token", extra={"reason": type(exc).__name__})
        return None
