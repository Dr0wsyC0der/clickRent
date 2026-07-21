from sqlalchemy import select
from app.models.properties import Property as PropertyModel
from typing import List
from app.repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    async def get_by_id(self, property_id: int) -> PropertyModel | None:
        result = await self.session.scalars(select(PropertyModel).where(PropertyModel.id == property_id))
        return result.first()

    async def get_all(self) -> List[PropertyModel]:
        result = await self.session.scalars(select(PropertyModel))
        return result.all()

    async def create(self, property: PropertyModel) -> PropertyModel | None:
        self.session.add(property)
        await self.session.commit()
        await self.session.refresh(property)
        return property

    async def update(self, property: PropertyModel) -> PropertyModel | None:
        await self.session.commit()
        await self.session.refresh(property)
        return property

    async def delete(self, property: PropertyModel) -> PropertyModel | None:
        await self.session.delete(property)
        await self.session.commit()

