from fastapi import Depends
from app.repositories.property import PropertyRepository
from app.services.property import PropertyService
from app.api.dependencies.repositories import get_property_repository



async def get_property_service(
        property_repository: PropertyRepository = Depends(get_property_repository)
        ) -> PropertyService:
    return PropertyService(property_repository=property_repository)