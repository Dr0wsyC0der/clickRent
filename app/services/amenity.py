from app.repositories.amenity import AmenityRepository
from app.models.amenities import Amenity as AmenityModel
from app.exceptions.amenity import AmenityNotFoundException

class AmenityService:
    def __init__(self, amenity_repository: AmenityRepository):
        self.amenity_repository = amenity_repository

    async def get_amenity_by_id(self, amenity_id: int) -> AmenityModel:
        amenity = await self.amenity_repository.get_by_id(amenity_id)
        if not amenity:
            raise AmenityNotFoundException("Удобство не найдено")
        return amenity

    async def get_all_amenities(self) -> list[AmenityModel]:
        return await self.amenity_repository.get_all()