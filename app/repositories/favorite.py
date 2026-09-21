from app.repositories.base import BaseRepository
from app.models.favorite import Favorite as FavoriteModel
from app.models.properties import Property as PropertyModel
from sqlalchemy import select, and_, func



class FavoriteRepository(BaseRepository):
    async def check_if_favorite(self, user_id: int, property_id: int) -> FavoriteModel | None:
        result = await self.session.scalars(
            select(FavoriteModel).where(
                and_(
                    FavoriteModel.user_id == user_id,
                    FavoriteModel.property_id == property_id
                )
            )
        )
        return result.first() 

    async def add_favorite(self, favorite: FavoriteModel) -> FavoriteModel:
        self.session.add(favorite)
        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def remove_favorite(self, favorite: FavoriteModel) -> None:
        await self.session.delete(favorite)
        await self.session.commit()

    async def get_user_favorites(self,user_id: int,page: int,size: int,) -> tuple[list[PropertyModel], int]:
        count_query = (
            select(func.count())
            .select_from(FavoriteModel)
            .where(FavoriteModel.user_id == user_id)
        )
        total = await self.session.scalar(count_query)
        result = await self.session.scalars(
            select(PropertyModel)
            .join(FavoriteModel)
            .where(FavoriteModel.user_id == user_id)
            .offset((page - 1) * size)
            .limit(size)
        )
        properties = result.all()
        return properties, total