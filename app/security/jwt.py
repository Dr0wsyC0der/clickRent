from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from typing import Any


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

def create_access_token(data: dict) -> str:
    return _create_token(
        data,
        timedelta(minutes=settings.access_token_expire_minutes),
    )

def create_refresh_token(data: dict) -> str:
    return _create_token(
        data,
        timedelta(days=settings.refresh_token_expire_days),
    )

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )