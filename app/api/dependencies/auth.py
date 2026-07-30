from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth import AuthService
from app.security.jwt import decode_token
from app.api.dependencies.repositories import get_refresh_token_repository, get_user_repository
from app.api.dependencies.db import get_session
from app.exceptions.auth import InvalidCredentialsException
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
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