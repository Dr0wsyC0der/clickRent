from app.repositories.amenity import AmenityRepository
from app.services.amenity import AmenityService
from app.api.dependencies.repositories import get_amenity_repository
from fastapi import Depends

async def get_amenity_service(
        amenity_repository: AmenityRepository = Depends(get_amenity_repository)
        ) -> AmenityService:
    return AmenityService(amenity_repository=amenity_repository)