from fastapi import Depends

from app.services.property_view import PropertyViewService
from app.repositories.property_view import PropertyViewRepository
from app.api.dependencies.repositories import get_property_view_repository


async def get_property_view_service(property_view_repository: PropertyViewRepository = Depends(get_property_view_repository)) -> PropertyViewService:
    return PropertyViewService(property_view_repository = property_view_repository)
