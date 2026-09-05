from app.repositories.favorite import FavoriteRepository
from app.repositories.property import PropertyRepository
from app.models.favorite import Favorite as FavoriteModel
from app.models.properties import Property as PropertyModel
from app.exceptions.favorite import AlreadyAddedToFavoritesException, FavoriteNotFoundException
from app.exceptions.property import PropertyNotFoundException
class FavoriteService:
    def __init__(self, favorite_repository: FavoriteRepository, property_repository: PropertyRepository):
        self.favorite_repository = favorite_repository
        self.property_repository = property_repository

    async def add_favorite(self, user_id: int, property_id: int) -> None:
        property = await self.property_repository.get_by_id(property_id)
        if not property:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
        
        is_favorite = await self.favorite_repository.check_if_favorite(user_id, property_id)
        if is_favorite:
            raise AlreadyAddedToFavoritesException("Недвижимость уже добавлена в избранное.")
        favorite = FavoriteModel(user_id=user_id, property_id=property_id)
        await self.favorite_repository.add_favorite(favorite)

    async def remove_favorite(self, user_id: int, property_id: int) -> None:
        favorite = await self.favorite_repository.check_if_favorite(user_id, property_id)
        if not favorite:
            raise FavoriteNotFoundException("Недвижимость не найдена в избранном.")
        await self.favorite_repository.remove_favorite(favorite)

    async def get_user_favorites(self, user_id: int) -> list[PropertyModel]:    
        return await self.favorite_repository.get_user_favorites(user_id)