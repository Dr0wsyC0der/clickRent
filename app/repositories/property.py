from sqlalchemy import select, func, exists, and_, insert, delete
from app.models.properties import Property as PropertyModel
from app.repositories.base import BaseRepository
from app.schemas.property import PropertySearchParams, PropertyListParams, PropertySortBy
from app.models.property_views import PropertyView as PropertyViewModel
from app.models.bookings import Booking as BookingModel
from app.models.amenities import Amenity as AmenityModel
from app.models.association_tables import property_amenities as PropertyAmenitiesModel
from app.repositories.booking import active_booking_condition
from datetime import date, datetime, timedelta, timezone

POPULARITY_WINDOW_DAYS = 30


class PropertyRepository(BaseRepository):
    async def get_by_id(self, property_id: int) -> PropertyModel | None:
        result = await self.session.scalars(select(PropertyModel).where(PropertyModel.id == property_id))
        return result.first()

    async def get_by_id_for_update(self, property_id: int) -> PropertyModel | None:
        # Блокировка строки объекта сериализует конкурентные бронирования одного объекта
        result = await self.session.scalars(
            select(PropertyModel)
            .where(PropertyModel.id == property_id)
            .with_for_update()
        )
        return result.first()

    async def get_all(self, filters: PropertyListParams) -> tuple[list[PropertyModel], int]:
        count_query = select(func.count()).select_from(PropertyModel)
        total = await self.session.scalar(count_query)

        result = await self.session.scalars(
            select(PropertyModel)
            .order_by(PropertyModel.created_at.desc())
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
            conditions.append(func.lower(PropertyModel.city) == filters.city.strip().lower())

        if filters.country is not None:
            conditions.append(func.lower(PropertyModel.country) == filters.country.strip().lower())

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
            conditions.append(PropertyModel.rooms >= filters.rooms)

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
                    active_booking_condition(datetime.now(timezone.utc)),
                )
            )

            conditions.append(~booking_exists)

        if filters.amenity_ids:
            amenity_ids = set(filters.amenity_ids)
            # Объект должен иметь все запрошенные удобства
            properties_with_amenities = (
                select(PropertyAmenitiesModel.c.property_id)
                .where(PropertyAmenitiesModel.c.amenity_id.in_(amenity_ids))
                .group_by(PropertyAmenitiesModel.c.property_id)
                .having(func.count(PropertyAmenitiesModel.c.amenity_id.distinct()) == len(amenity_ids))
            )
            conditions.append(PropertyModel.id.in_(properties_with_amenities))

        count_query = select(func.count()).select_from(PropertyModel).where(*conditions)
        total = await self.session.scalar(count_query)
        
        result = await self.session.scalars(
            select(PropertyModel)
            .where(*conditions)
            .order_by(*self._search_ordering(filters.sort_by))
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )

        properties = result.all()

        return properties, total

    @staticmethod
    def _search_ordering(sort_by: PropertySortBy) -> list:
        if sort_by == PropertySortBy.PRICE_ASC:
            ordering = [PropertyModel.price_per_night.asc()]
        elif sort_by == PropertySortBy.PRICE_DESC:
            ordering = [PropertyModel.price_per_night.desc()]
        elif sort_by == PropertySortBy.RATING:
            ordering = [PropertyModel.rating.desc().nulls_last(), PropertyModel.review_count.desc()]
        elif sort_by == PropertySortBy.POPULARITY:
            # Популярность — уникальные просмотры за последние 30 дней
            views_last_month = (
                select(func.count())
                .select_from(PropertyViewModel)
                .where(
                    PropertyViewModel.property_id == PropertyModel.id,
                    PropertyViewModel.view_date >= date.today() - timedelta(days=POPULARITY_WINDOW_DAYS),
                )
                .scalar_subquery()
            )
            ordering = [views_last_month.desc()]
        else:
            ordering = []

        # Стабильный порядок для пагинации
        return [*ordering, PropertyModel.created_at.desc(), PropertyModel.id.desc()]

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