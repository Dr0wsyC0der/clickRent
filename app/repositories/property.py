from sqlalchemy import select, func, exists, and_, insert, delete
from app.models.properties import Property as PropertyModel
from app.repositories.base import BaseRepository
from app.schemas.property import PropertySearchParams, PropertyListParams
from app.models.bookings import Booking as BookingModel
from app.models.amenities import Amenity as AmenityModel
from app.models.association_tables import property_amenities as PropertyAmenitiesModel
from app.db.enums import BookingStatus


class PropertyRepository(BaseRepository):
    async def get_by_id(self, property_id: int) -> PropertyModel | None:
        result = await self.session.scalars(select(PropertyModel).where(PropertyModel.id == property_id))
        return result.first()

    async def get_all(self, filters: PropertyListParams) -> tuple[list[PropertyModel], int]:
        count_query = select(func.count()).select_from(PropertyModel)
        total = await self.session.scalar(count_query)

        result = await self.session.scalars(
            select(PropertyModel)
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )

        return result.all(), total

    async def create(self, property: PropertyModel) -> PropertyModel | None:
        self.session.add(property)
        await self.session.flush()
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

    async def get_host_properties(self, owner_id: int) -> list[PropertyModel]:
        result = await self.session.scalars(
            select(PropertyModel).where(PropertyModel.owner_id == owner_id)
        )
        return result.all()

    async def search_properties(self, filters: PropertySearchParams) -> tuple[list[PropertyModel], int]:
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

        if filters.check_in and filters.check_out:
            booking_exists = exists().where(
                and_(
                    BookingModel.property_id == PropertyModel.id,
                    BookingModel.check_in < filters.check_out,
                    BookingModel.check_out > filters.check_in,
                    BookingModel.status.in_([
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                    ])
                )
            )

            conditions.append(~booking_exists)

        count_query = select(func.count()).select_from(PropertyModel).where(*conditions)
        total = await self.session.scalar(count_query)
        
        result = await self.session.scalars(
            select(PropertyModel).where(*conditions).offset((filters.page - 1) * filters.size).limit(filters.size)
        )

        properties = result.all()

        return properties, total

    async def get_property_amenities(self, property_id: int) -> list[AmenityModel]:
        result =  await self.session.scalars(
            select(AmenityModel).join(PropertyAmenitiesModel, AmenityModel.id == PropertyAmenitiesModel.c.amenity_id)
            .where(PropertyAmenitiesModel.c.property_id == property_id))
        return result.all()

    async def add_amenity_to_property(self, property_id: int, amenity_id: int) -> None:
        query = insert(PropertyAmenitiesModel).values(
            property_id=property_id,
            amenity_id=amenity_id,
        )

        await self.session.execute(query)


    async def remove_amenity_from_property(self,property_id: int, amenity_id: int) -> None:
        query = delete(PropertyAmenitiesModel).where(
        PropertyAmenitiesModel.c.property_id == property_id,
        PropertyAmenitiesModel.c.amenity_id == amenity_id,
        )

        await self.session.execute(query)  