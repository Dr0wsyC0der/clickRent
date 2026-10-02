from datetime import datetime, timezone
from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.notification import NotificationService
from app.schemas.review import CreateReview, UpdateReview
from app.models.reviews import Review as ReviewModel
from app.exceptions.review import ReviewAlreadyExistsException, ReviewNotFoundException, ReviewAccessDeniedException
from app.db.enums import BookingStatus, NotificationType

class ReviewService:
    def __init__(
        self,
        review_repository: ReviewRepository,
        booking_repository: BookingRepository,
        property_repository: PropertyRepository,
        notification_service: NotificationService,
    ):
        self.review_repository = review_repository
        self.booking_repository = booking_repository
        self.property_repository = property_repository
        self.notification_service = notification_service

    async def create_review(self, user_id: int, review_data: CreateReview) -> ReviewModel:
        booking = await self.booking_repository.get_booking_by_id(review_data.booking_id)
        if not booking:
            raise ReviewNotFoundException("Бронирование с указанным ID не найдено.")
        if booking.guest_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для создания отзыва для этого бронирования.")
        # Проживание считается состоявшимся, если бронь завершена или подтверждена и дата выезда уже прошла
        # (фоновая задача переводит такие брони в COMPLETED с задержкой)
        stay_finished = booking.status == BookingStatus.COMPLETED or (
            booking.status == BookingStatus.CONFIRMED
            and booking.check_out <= datetime.now(timezone.utc)
        )
        if not stay_finished:
            raise ReviewAccessDeniedException("Отзыв можно оставить только после завершенного проживания.")
        if booking.property_id != review_data.property_id:
            raise ReviewAccessDeniedException("Отзыв можно оставить только для недвижимости, связанной с бронированием.")
        existing_review = await self.review_repository.get_by_booking_id(review_data.booking_id)
        if existing_review:
            raise ReviewAlreadyExistsException("Отзыв для данного бронирования уже существует.")
        review_values = review_data.model_dump()
        new_review = ReviewModel(
            **review_values,
            author_id=user_id,
        )
        try:
            new_review = await self.review_repository.create(new_review)
            await self.review_repository.refresh_property_rating(new_review.property_id)
            await self.review_repository.commit()
        except Exception:
            await self.review_repository.rollback()
            raise

        review_property = await self.property_repository.get_by_id(new_review.property_id)
        if review_property is not None:
            await self.notification_service.create_notification(
                user_id=review_property.owner_id,
                notification_type=NotificationType.NEW_REVIEW,
                title="Новый отзыв",
                message=f"Гость оставил отзыв с оценкой {float(new_review.rating):g} об объекте «{review_property.title}».",
            )

        return new_review

    async def get_review_by_id(self, review_id: int) -> ReviewModel | None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        return review

    async def get_property_reviews(self,property_id: int,page: int,size: int,) -> tuple[list[ReviewModel], int]:
        return await self.review_repository.get_property_reviews(
            property_id=property_id,
            page=page,
            size=size,
        )
    async def update_review(self, user_id: int, review_id: int, review_data: UpdateReview) -> ReviewModel | None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        if review.author_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для изменения этого отзыва.")
        for key, value in review_data.model_dump(exclude_unset=True).items():
            setattr(review, key, value)
        try:
            review = await self.review_repository.update(review)
            await self.review_repository.refresh_property_rating(review.property_id)
            await self.review_repository.commit()
        except Exception:
            await self.review_repository.rollback()
            raise
        return review

    async def delete_review(self, user_id: int, review_id: int) -> None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        if review.author_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для управления этим отзывом.")
        property_id = review.property_id
        try:
            await self.review_repository.delete(review)
            await self.review_repository.refresh_property_rating(property_id)
            await self.review_repository.commit()
        except Exception:
            await self.review_repository.rollback()
            raise
