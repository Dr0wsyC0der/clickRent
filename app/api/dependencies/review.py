from fastapi import Depends
from app.services.review import ReviewService
from app.services.notification import NotificationService
from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.api.dependencies.notification import get_notification_service
from app.api.dependencies.cache import get_property_cache
from app.cache.property import PropertyCache
from app.api.dependencies.repositories import get_review_repository, get_booking_repository, get_property_repository

async def get_review_service(
        review_repository: ReviewRepository = Depends(get_review_repository),
        booking_repository: BookingRepository = Depends(get_booking_repository),
        property_repository: PropertyRepository = Depends(get_property_repository),
        notification_service: NotificationService = Depends(get_notification_service),
        property_cache: PropertyCache = Depends(get_property_cache),
        ) -> ReviewService:
    return ReviewService(
        review_repository=review_repository,
        booking_repository=booking_repository,
        property_repository=property_repository,
        notification_service=notification_service,
        property_cache=property_cache,
    )
