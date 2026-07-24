from fastapi import APIRouter, Depends, status
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.api.dependencies.auth import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
    ):

    user = await auth_service.register(data)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
    ):

    token = await auth_service.login(data)
    return token

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
    ):

    token = await auth_service.refresh(data.refresh_token)
    return token

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
    ):

    await auth_service.logout(data.refresh_token)

    