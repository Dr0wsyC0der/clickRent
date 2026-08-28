from sqlalchemy import select
from app.models.reviews import Review as ReviewModel

from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository):
    async def create(self, review: ReviewModel) -> ReviewModel:
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def get_by_id(self, review_id: int) -> ReviewModel | None:
        result = await self.session.scalars(select(ReviewModel).where(ReviewModel.id == review_id))
        return result.first()

    async def get_by_booking_id(self, booking_id: int) -> ReviewModel | None:
        result = await self.session.scalars(select(ReviewModel).where(ReviewModel.booking_id == booking_id))
        return result.first()

    async def get_property_reviews(self, property_id: int) -> list[ReviewModel]:
        result = await self.session.scalars(select(ReviewModel).where(ReviewModel.property_id == property_id))
        return result.all() 

    async def update(self, review: ReviewModel) -> ReviewModel:
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def delete(self, review: ReviewModel) -> None:
        await self.session.delete(review)
        await self.session.commit()

    