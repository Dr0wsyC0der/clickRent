from app.repositories.property import PropertyRepository
from app.repositories.booking import BookingRepository
from app.repositories.amenity import AmenityRepository
from app.cache.property import PropertyCache
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertySearchParams, PropertyListParams, PropertyResponse, PropertySortBy
from app.models.properties import Property as PropertyModel
from app.models.amenities import Amenity as AmenityModel
from app.exceptions.property import PropertyAlreadyExistsException, PropertyNotFoundException, PropertyAccessDeniedException
from app.exceptions.amenity import AmenityNotFoundException, AmenityAlreadyAddedException, AmenityNotAddedException

class PropertyService:
    def __init__(
        self,
        property_repository: PropertyRepository,
        booking_repository: BookingRepository,
        amenity_repository: AmenityRepository,
        property_cache: PropertyCache,
    ):
        self.property_repository = property_repository
        self.booking_repository = booking_repository
        self.amenity_repository = amenity_repository
        self.property_cache = property_cache

    async def create_property(self, user_id: int, property_data: PropertyCreate) -> PropertyModel:
        existing_property = await self.property_repository.get_by_owner_and_address(
            owner_id=user_id,
            city=property_data.city,
            address=property_data.address
        )
        if existing_property:
            raise PropertyAlreadyExistsException("Недвижимость с таким адресом уже существует для данного пользователя.")
        property_values = property_data.model_dump(exclude={"amenity_ids"})
        new_property = PropertyModel(
             **property_values,
            owner_id=user_id,
        )
        
        amenity_ids = property_data.amenity_ids
        if amenity_ids is not None:
            amenities = await self.amenity_repository.get_by_ids(amenity_ids)

            if len(amenity_ids) != len(amenities):
                    raise AmenityNotFoundException("Одно или несколько удобств не найдены")
        try: 
            new_property = await self.property_repository.create(new_property)

            if amenity_ids is not None:
                for amenity in amenities:
                    await self.property_repository.add_amenity_to_property(property_id=new_property.id, amenity_id=amenity.id)
            await self.property_repository.commit()
        except Exception:
             await self.property_repository.rollback()
             raise
        
        await self.property_cache.invalidate_catalog()
        return new_property


    async def get_all_properties(self, filters: PropertyListParams) -> tuple[list[PropertyModel | PropertyResponse], int]:
        return await self.property_cache.get_catalog_page(
            "list", filters, lambda: self.property_repository.get_all(filters)
        )

    async def get_property_by_id(self, property_id: int) -> PropertyModel | PropertyResponse:
        property = await self.property_cache.get_property(
            property_id, lambda: self.property_repository.get_by_id(property_id)
        )
        if not property:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
        return property

    async def get_host_properties(self, owner_id: int) -> list[PropertyModel]:
        return await self.property_repository.get_host_properties(owner_id)

    async def update_property(self, owner_id: int, property_id: int, property_data: PropertyUpdate) -> PropertyModel | None:
        property = await self.property_repository.get_by_id(property_id)
        if not property:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
        if property.owner_id != owner_id:
            raise PropertyAccessDeniedException("У вас нет прав для изменения этой недвижимости.")
        for key, value in property_data.model_dump(exclude_unset=True).items():
            setattr(property, key, value)
        updated_property = await self.property_repository.update(property)
        await self.property_cache.invalidate_property(property_id)
        return updated_property

    async def delete_property(self, owner_id: int, property_id: int) -> None:
        property = await self.property_repository.get_by_id(property_id)
        if not property:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
        if property.owner_id != owner_id:
            raise PropertyAccessDeniedException("У вас нет прав для управления этой недвижимостью.")
        await self.property_repository.delete(property)
        await self.property_cache.invalidate_property(property_id)

    async def search_properties(self, filters: PropertySearchParams) -> tuple[list[PropertyModel | PropertyResponse], int]:
        # Доступность по датам зависит от бронирований, а популярность — от каждого просмотра:
        # такие результаты меняются без изменения объектов, поэтому не кэшируются
        if filters.check_in is not None or filters.sort_by == PropertySortBy.POPULARITY:
            return await self.property_repository.search_properties(filters)

        return await self.property_cache.get_catalog_page(
            "search", filters, lambda: self.property_repository.search_properties(filters)
        )

    async def add_amenity_to_property(self, owner_id: int, property_id: int, amenity_id: int) -> None:
        property_obj = await self.property_repository.get_by_id(property_id)
        if not property_obj: 
            raise PropertyNotFoundException("Недвижимость не найдена")
        if property_obj.owner_id != owner_id:
            raise PropertyAccessDeniedException("У вас нет прав для доступа к этой недвиждимости")
        amenity = await self.amenity_repository.get_by_id(amenity_id)
        if not amenity:
            raise AmenityNotFoundException("Удобство не найдено")
        amenities = await self.property_repository.get_property_amenities(property_id)
        if any(amenity.id == amenity_id for amenity in amenities):
            raise AmenityAlreadyAddedException(
                "Удобство уже добавлено к этой недвижимости"
            )
        try:
            await self.property_repository.add_amenity_to_property(
                property_id,
                amenity_id,
            )
            await self.property_repository.commit()
        except Exception:
            await self.property_repository.rollback()
            raise

        # Удобства влияют на результаты поиска с фильтром amenity_ids
        await self.property_cache.invalidate_catalog()

    async def get_property_amenities(self, property_id: int) -> list[AmenityModel]:
        property_obj = await self.property_repository.get_by_id(property_id)

        if not property_obj:
            raise PropertyNotFoundException("Недвижимость не найдена")

        return await self.property_repository.get_property_amenities(property_id)

    async def remove_amenity_from_property(self,owner_id: int, property_id: int ,amenity_id: int,) -> None:
        property_obj = await self.property_repository.get_by_id(property_id)
        if not property_obj:
                raise PropertyNotFoundException("Недвижимость не найдена")
        if property_obj.owner_id != owner_id:
                raise PropertyAccessDeniedException("У вас нет прав для доступа к этой недвиждимости")

        amenity = await self.amenity_repository.get_by_id(amenity_id)
        if not amenity:
                raise AmenityNotFoundException("Удобство не найдено")
        amenities = await self.property_repository.get_property_amenities(property_id)
        if not any(amenity.id == amenity_id for amenity in amenities):
                    raise AmenityNotAddedException("У этой недвижимости нет одного или несколько из этих удобств")

        try:
            await self.property_repository.remove_amenity_from_property(
                property_id,
                amenity_id,
            )
            await self.property_repository.commit()
        except Exception:
            await self.property_repository.rollback()
            raise

        await self.property_cache.invalidate_catalog()
