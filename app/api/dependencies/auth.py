from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth import AuthService
from app.api.dependencies.repositories import get_refresh_token_repository, get_user_repository
from fastapi import Depends

async def get_auth_service(
        user_repository: UserRepository = Depends(get_user_repository),
        refresh_token_repository: RefreshTokenRepository = Depends(get_refresh_token_repository)
        ) -> AuthService:
    return AuthService(user_repository=user_repository, refresh_token_repository=refresh_token_repository)