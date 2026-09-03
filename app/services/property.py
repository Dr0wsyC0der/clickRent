from app.repositories.property import PropertyRepository
from app.repositories.booking import BookingRepository
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertySearchParams, PropertyListParams
from app.models.properties import Property as PropertyModel
from app.exceptions.property import PropertyAlreadyExistsException, PropertyNotFoundException, PropertyAccessDeniedException

class PropertyService:
    def __init__(self, property_repository: PropertyRepository, booking_repository: BookingRepository):
        self.property_repository = property_repository
        self.booking_repository = booking_repository

    async def create_property(self, user_id: int, property_data: PropertyCreate) -> PropertyModel:
        existing_property = await self.property_repository.get_by_owner_and_address(
            owner_id=user_id,
            city=property_data.city,
            address=property_data.address
        )
        if existing_property:
            raise PropertyAlreadyExistsException("Недвижимость с таким адресом уже существует для данного пользователя.")
        property_values = property_data.model_dump()
        new_property = PropertyModel(
             **property_values,
            owner_id=user_id,
        )
        return await self.property_repository.create(new_property)

    async def get_all_properties(self, filters: PropertyListParams) -> tuple[list[PropertyModel], int]:
        return await self.property_repository.get_all(filters)

    async def get_property_by_id(self, property_id: int) -> PropertyModel | None:
        property = await self.property_repository.get_by_id(property_id)
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
        return await self.property_repository.update(property)

    async def delete_property(self, owner_id: int, property_id: int) -> None:
        property = await self.property_repository.get_by_id(property_id)
        if not property:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
        if property.owner_id != owner_id:
            raise PropertyAccessDeniedException("У вас нет прав для управления этой недвижимостью.")
        await self.property_repository.delete(property)

    async def search_properties(self, filters: PropertySearchParams) -> tuple[list[PropertyModel], int]:
        properties, total = await self.property_repository.search_properties(filters)
        return properties, total