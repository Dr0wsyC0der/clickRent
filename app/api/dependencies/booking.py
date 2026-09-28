from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.notification import NotificationService
from app.services.booking import BookingService
from app.api.dependencies.notification import get_notification_service
from app.api.dependencies.repositories import get_booking_repository, get_property_repository
from fastapi import Depends

async def get_booking_service(
        booking_repository: BookingRepository = Depends(get_booking_repository),
        property_repository: PropertyRepository = Depends(get_property_repository),
        notification_service: NotificationService = Depends(get_notification_service)
        ) -> BookingService:
    return BookingService(
        booking_repository=booking_repository,
        property_repository=property_repository,
        notification_service=notification_service,
    )