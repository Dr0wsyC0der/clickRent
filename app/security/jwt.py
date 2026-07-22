from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from app.exceptions.auth import InvalidRefreshTokenException
from typing import Any


def _create_token(data: dict, expires_delta: timedelta) -> tuple[str, datetime]:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire

    token = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return token, expire

def create_access_token(data: dict) -> tuple[str, datetime]:
    payload = data.copy()
    payload["type"] = "access"

    return _create_token(
        payload,
        timedelta(minutes=settings.access_token_expire_minutes),
    )

def create_refresh_token(data: dict) -> tuple[str, datetime]:
    payload = data.copy()
    payload["type"] = "refresh"

    return _create_token(
        payload,
        timedelta(days=settings.refresh_token_expire_days),
    )

def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise InvalidRefreshTokenException() from exc