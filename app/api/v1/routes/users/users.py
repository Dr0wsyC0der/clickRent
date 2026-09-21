from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService
from app.api.dependencies.auth import get_current_user, get_auth_service
from app.models.users import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])



@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.update_me(
        user=current_user,
        user_data=user_data,
    )