from sqlalchemy import select, and_
from app.models.properties import Property as PropertyModel
from typing import List
from app.repositories.base import BaseRepository
from app.schemas.property import PropertySearchParams


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

    async def delete(self, property: PropertyModel) -> None:
        await self.session.delete(property)
        await self.session.commit()

    async def get_by_owner_and_address(self, owner_id: int, city: str, address: str) -> PropertyModel | None:
        result = await self.session.scalars(
            select(PropertyModel).where(
                PropertyModel.owner_id == owner_id,
                PropertyModel.city == city,
                PropertyModel.address == address
            )
        )
        return result.first()

    async def get_host_properties(self, owner_id: int) -> List[PropertyModel]:
        result = await self.session.scalars(
            select(PropertyModel).where(PropertyModel.owner_id == owner_id)
        )
        return result.all()

    async def search_properties(self, filters: PropertySearchParams) -> List[PropertyModel]:

        conditions = []

        if filters.city is not None:
            conditions.append(PropertyModel.city == filters.city)

        if filters.country is not None:
            conditions.append(PropertyModel.country == filters.country)

        if filters.min_price is not None:
            conditions.append(
                PropertyModel.price_per_night >= filters.min_price
            )

        if filters.max_price is not None:
            conditions.append(
                PropertyModel.price_per_night <= filters.max_price
            )

        if filters.guest_capacity is not None:
            conditions.append(
                PropertyModel.guest_capacity >= filters.guest_capacity
            )

        if filters.rooms is not None:
            conditions.append(PropertyModel.rooms == filters.rooms)

        if filters.beds is not None:
            conditions.append(PropertyModel.beds >= filters.beds)

        if filters.bathrooms is not None:
            conditions.append(PropertyModel.bathrooms >= filters.bathrooms)

        if filters.rating is not None:
            conditions.append(PropertyModel.rating >= filters.rating)

        result = await self.session.scalars(
            select(PropertyModel).where(*conditions)
        )

        return result.all()
        
