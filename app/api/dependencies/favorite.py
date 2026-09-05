from fastapi import Depends
from app.services.favorite import FavoriteService
from app.api.dependencies.repositories import get_favorite_repository, FavoriteRepository, get_property_repository, PropertyRepository

async def get_favorite_service(
        favorite_repository: FavoriteRepository = Depends(get_favorite_repository),
        property_repository: PropertyRepository = Depends(get_property_repository)
        ) -> FavoriteService:
    return FavoriteService(favorite_repository=favorite_repository, property_repository=property_repository)