from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth import AuthService
from app.security.jwt import decode_token
from app.api.dependencies.repositories import get_refresh_token_repository, get_user_repository
from app.api.dependencies.db import get_session
from app.exceptions.auth import InvalidCredentialsException, AdminAccessDeniedException, AccessDeniedException
from app.db.enums import UserRole
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)
async def get_auth_service(
        user_repository: UserRepository = Depends(get_user_repository),
        refresh_token_repository: RefreshTokenRepository = Depends(get_refresh_token_repository)
        ) -> AuthService:
    return AuthService(user_repository=user_repository, refresh_token_repository=refresh_token_repository)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
):
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise InvalidCredentialsException()

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise InvalidCredentialsException()

    user = await user_repository.get_by_id(user_id)

    if user is None:
        raise InvalidCredentialsException()

    return user

async def check_admin(current_user = Depends(get_current_user)) -> None:
    if current_user.role != UserRole.ADMIN:
        raise AdminAccessDeniedException()

async def check_host(current_user = Depends(get_current_user)) -> None:
    if current_user.role != UserRole.HOST:
        raise AccessDeniedException()

async def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
):
    if not token:
        return None

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            return None

        user_id = int(payload["sub"])

        user = await user_repository.get_by_id(user_id)

        return user

    except (InvalidCredentialsException, KeyError, ValueError):
        return None