from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.models.property_views import PropertyView as PropertyViewModel
from app.repositories.base import BaseRepository


class PropertyViewRepository(BaseRepository):
    async def create_view(self, view: PropertyViewModel) -> None:
        query = (
            insert(PropertyViewModel)
            .values(
                user_id=view.user_id,
                visitor_id=view.visitor_id,
                property_id=view.property_id,
                view_date=view.view_date,
            )
            .on_conflict_do_nothing()
        )

        await self.session.execute(query)

    async def get_property_views(self,property_id: int) -> list[PropertyViewModel]:
        result = await self.session.scalars(
            select(PropertyViewModel)
            .where(PropertyViewModel.property_id == property_id)
            .order_by(PropertyViewModel.created_at.desc())
        )

        return result.all()

    async def count_property_views(self, property_id: int) -> int:
        result = await self.session.scalar(
            select(func.count())
            .select_from(PropertyViewModel)
            .where(PropertyViewModel.property_id == property_id)
        )

        return result or 0