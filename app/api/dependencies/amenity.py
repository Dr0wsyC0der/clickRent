from app.repositories.amenity import AmenityRepository
from app.services.amenity import AmenityService
from app.api.dependencies.repositories import get_amenity_repository
from app.api.dependencies.cache import get_property_cache
from app.cache.property import PropertyCache
from fastapi import Depends

async def get_amenity_service(
        amenity_repository: AmenityRepository = Depends(get_amenity_repository),
        property_cache: PropertyCache = Depends(get_property_cache),
        ) -> AmenityService:
    return AmenityService(amenity_repository=amenity_repository, property_cache=property_cache)