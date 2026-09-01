from fastapi import Depends

from app.services.property import PropertyService
from app.repositories.property import PropertyRepository
from app.repositories.booking import BookingRepository
from app.api.dependencies.repositories import (
    get_property_repository,
    get_booking_repository
)


async def get_property_service(
    property_repository: PropertyRepository = Depends(get_property_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository)
) -> PropertyService:
    return PropertyService(
        property_repository=property_repository,
        booking_repository=booking_repository
    )