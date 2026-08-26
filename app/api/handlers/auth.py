from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.auth import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    RefreshTokenExpiredException,
    RefreshTokenRevokedException,
    AdminAccessDeniedException,
    AccessDeniedException
)


async def email_exists_handler(request: Request, exc: EmailAlreadyExistsException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Email already exists"},
    )


async def username_exists_handler(request: Request, exc: UsernameAlreadyExistsException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Username already exists"},
    )


async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsException):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid credentials"},
    )


async def invalid_refresh_token_handler(request: Request, exc: InvalidRefreshTokenException):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid refresh token"},
    )


async def refresh_token_expired_handler(request: Request, exc: RefreshTokenExpiredException):
    return JSONResponse(
        status_code=401,
        content={"detail": "Refresh token expired"},
    )


async def refresh_token_revoked_handler(request: Request, exc: RefreshTokenRevokedException):
    return JSONResponse(
        status_code=401,
        content={"detail": "Refresh token revoked"},
    )

async def admin_access_denied_handler(request: Request, exc: AdminAccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": "Admin access denied"},
    )

async def access_denied_handler(request: Request, exc: AccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": "Access denied"},
    )