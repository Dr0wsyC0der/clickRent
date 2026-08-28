from fastapi import Depends
from app.services.review import ReviewService
from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.api.dependencies.repositories import get_review_repository, get_booking_repository

async def get_review_service(
        review_repository: ReviewRepository = Depends(get_review_repository),
        booking_repository: BookingRepository = Depends(get_booking_repository)
        ) -> ReviewService:
    return ReviewService(review_repository=review_repository, booking_repository=booking_repository)