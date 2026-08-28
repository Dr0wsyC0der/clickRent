from app.repositories.review import ReviewRepository
from app.repositories.booking import BookingRepository
from app.schemas.review import CreateReview, UpdateReview
from app.models.reviews import Review as ReviewModel
from app.exceptions.review import ReviewAlreadyExistsException, ReviewNotFoundException, ReviewAccessDeniedException
from app.db.enums import BookingStatus

class ReviewService:
    def __init__(self, review_repository: ReviewRepository, booking_repository: BookingRepository):
        self.review_repository = review_repository
        self.booking_repository = booking_repository

    async def create_review(self, user_id: int, review_data: CreateReview) -> ReviewModel:
        booking = await self.booking_repository.get_booking_by_id(review_data.booking_id)
        if not booking:
            raise ReviewNotFoundException("Бронирование с указанным ID не найдено.")
        if booking.guest_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для создания отзыва для этого бронирования.")
        if booking.status != BookingStatus.COMPLETED:
            raise ReviewAccessDeniedException("Отзыв можно оставить только для завершенных бронирования.")
        if booking.property_id != review_data.property_id:
            raise ReviewAccessDeniedException("Отзыв можно оставить только для недвижимости, связанной с бронированием.")
        exsisting_review = await self.review_repository.get_by_booking_id(review_data.booking_id)
        if exsisting_review:
            raise ReviewAlreadyExistsException("Отзыв для данного бронирования уже существует.")
        review_values = review_data.model_dump()
        new_review = ReviewModel(
            **review_values,
            author_id=user_id,
        )
        return await self.review_repository.create(new_review)

    async def get_review_by_id(self, review_id: int) -> ReviewModel | None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        return review

    async def get_property_reviews(self, property_id: int) -> list[ReviewModel]:
        return await self.review_repository.get_property_reviews(property_id)

    async def update_review(self, user_id: int, review_id: int, review_data: UpdateReview) -> ReviewModel | None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        if review.author_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для изменения этого отзыва.")
        for key, value in review_data.model_dump(exclude_unset=True).items():
            setattr(review, key, value)
        return await self.review_repository.update(review)

    async def delete_review(self, user_id: int, review_id: int) -> None:
        review = await self.review_repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundException("Отзыв с указанным ID не найден.")
        if review.author_id != user_id:
            raise ReviewAccessDeniedException("У вас нет прав для управления этим отзывом.")
        await self.review_repository.delete(review)