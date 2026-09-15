from app.repositories.amenity import AmenityRepository
from app.models.amenities import Amenity as AmenityModel
from app.exceptions.amenity import AmenityNotFoundException, AmenityAlreadyAddedException
from app.schemas.amenity import AmenityCreate, AmenityUpdate

class AmenityService:
    def __init__(self, amenity_repository: AmenityRepository):
        self.amenity_repository = amenity_repository

    async def create_amenity(self, amenity_data: AmenityCreate) -> AmenityModel:
        existing_amenity = await self.amenity_repository.get_by_name(name=amenity_data.name)
        if existing_amenity:
            raise AmenityAlreadyAddedException("Такое удобство уже существует")
        new_amenity = AmenityModel(
            **amenity_data.model_dump()
        )
        try:
            await self.amenity_repository.create(amenity=new_amenity)
            await self.amenity_repository.commit()
        except Exception:
            await self.amenity_repository.rollback()
            raise

        return new_amenity

    async def update_amenity(self, amenity_id: int, amenity_data: AmenityUpdate) -> AmenityModel:
        existing_amenity = await self.amenity_repository.get_by_id(amenity_id=amenity_id)
        if not existing_amenity:
            raise AmenityNotFoundException("Удобство не найдено")

        if amenity_data.name:
            same_name_amenity = await self.amenity_repository.get_by_name(
                name=amenity_data.name
            )

            if same_name_amenity and same_name_amenity.id != amenity_id:
                raise AmenityAlreadyAddedException("Такое удобство уже существует")

        for key, value in amenity_data.model_dump(exclude_unset=True).items():
            setattr(existing_amenity, key, value)

        try:
            await self.amenity_repository.update(amenity=existing_amenity)
            await self.amenity_repository.commit()
        except Exception:
            await self.amenity_repository.rollback()
            raise

        return existing_amenity

    async def delete_amenity(self, amenity_id: int) -> None:
        amenity = await self.amenity_repository.get_by_id(amenity_id=amenity_id)
        if not amenity:
            raise AmenityNotFoundException("Удобство не найдено")

        try:
            await self.amenity_repository.delete(amenity=amenity)
            await self.amenity_repository.commit()
        except Exception:
            await self.amenity_repository.rollback()
            raise

    async def get_amenity_by_id(self, amenity_id: int) -> AmenityModel:
        amenity = await self.amenity_repository.get_by_id(amenity_id)
        if not amenity:
            raise AmenityNotFoundException("Удобство не найдено")
        return amenity

    async def get_all_amenities(self) -> list[AmenityModel]:
        return await self.amenity_repository.get_all()