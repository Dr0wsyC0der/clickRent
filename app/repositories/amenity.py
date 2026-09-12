from sqlalchemy import select
from app.models.amenities import Amenity as AmenityModel
from app.repositories.base import BaseRepository

class AmenityRepository(BaseRepository):
    async def get_by_id(self, amenity_id: int) -> AmenityModel|None:
        result = await self.session.scalars(select(AmenityModel).where(AmenityModel.id == amenity_id))
        return result.first()

    async def get_all(self) -> list[AmenityModel]:
        result = await self.session.scalars(select(AmenityModel))
        return result.all()

    async def get_by_ids(self, amenity_ids: list[int]) -> list[AmenityModel]:
        result = await self.session.scalars(
            select(AmenityModel).where(
                AmenityModel.id.in_(amenity_ids)
            )
        )
        return result.all()
