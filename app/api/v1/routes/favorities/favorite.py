from fastapi import APIRouter, Depends, status
from app.models.users import User
from app.services.favorite import FavoriteService
from app.api.dependencies.favorite import get_favorite_service
from app.api.dependencies.auth import get_current_user
from app.schemas.property import PropertyShortResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/{property_id}", status_code = status.HTTP_201_CREATED)
async def add_favorite(
    property_id: int,
    current_user: User = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    await favorite_service.add_favorite(current_user.id, property_id)
    return {"message": "Недвижимость успешно добавлена в избранное."}

@router.delete("/{property_id}", status_code = status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    property_id: int,
    current_user: User = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    await favorite_service.remove_favorite(current_user.id, property_id)

@router.get("/", response_model=list[PropertyShortResponse], status_code = status.HTTP_200_OK)
async def get_user_favorites(
    current_user: User = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    favorites = await favorite_service.get_user_favorites(current_user.id)
    return favorites