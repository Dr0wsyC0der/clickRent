from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.booking import BookingService
from app.api.dependencies.repositories import get_booking_repository, get_property_repository
from fastapi import Depends

async def get_booking_service(
        booking_repository: BookingRepository = Depends(get_booking_repository),
        property_repository: PropertyRepository = Depends(get_property_repository)
        ) -> BookingService:
    return BookingService(booking_repository=booking_repository, property_repository=property_repository)