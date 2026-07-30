from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.schemas.user import UserResponse

from app.models.users import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])



@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
):
    return current_user