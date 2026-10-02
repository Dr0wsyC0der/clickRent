from sqlalchemy import select, func, update
from app.models.reviews import Review as ReviewModel
from app.models.properties import Property as PropertyModel

from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository):
    async def create(self, review: ReviewModel) -> ReviewModel:
        self.session.add(review)
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def get_by_id(self, review_id: int) -> ReviewModel | None:
        result = await self.session.scalars(select(ReviewModel).where(ReviewModel.id == review_id))
        return result.first()

    async def get_by_booking_id(self, booking_id: int) -> ReviewModel | None:
        result = await self.session.scalars(select(ReviewModel).where(ReviewModel.booking_id == booking_id))
        return result.first()

    async def get_property_reviews(self,property_id: int,page: int,size: int,) -> tuple[list[ReviewModel], int]:
        count_query = (
            select(func.count())
            .select_from(ReviewModel)
            .where(ReviewModel.property_id == property_id)
        )
        total = await self.session.scalar(count_query)
        result = await self.session.scalars(
            select(ReviewModel)
            .where(ReviewModel.property_id == property_id)
            .order_by(ReviewModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        reviews = result.all()
        return reviews, total

    async def update(self, review: ReviewModel) -> ReviewModel:
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def delete(self, review: ReviewModel) -> None:
        await self.session.delete(review)
        await self.session.flush()

    async def refresh_property_rating(self, property_id: int) -> None:
        # Пересчет одним UPDATE по актуальным данным исключает рассинхронизацию при параллельных отзывах
        await self.session.execute(
            update(PropertyModel)
            .where(PropertyModel.id == property_id)
            .values(
                rating=(
                    select(func.round(func.avg(ReviewModel.rating), 2))
                    .where(ReviewModel.property_id == property_id)
                    .scalar_subquery()
                ),
                review_count=(
                    select(func.count())
                    .select_from(ReviewModel)
                    .where(ReviewModel.property_id == property_id)
                    .scalar_subquery()
                ),
            )
            .execution_options(synchronize_session="fetch")
        )
