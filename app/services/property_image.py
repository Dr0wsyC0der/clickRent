from app.repositories.property_image import PropertyImageRepository
from app.repositories.property import PropertyRepository
from app.models.property_images import PropertyImage as PropertyImageModel
from app.models.users import User as UserModel
from app.exceptions.property import PropertyNotFoundException
from app.exceptions.auth import AccessDeniedException
from app.exceptions.property_image import PropertyImageNotFoundException, PropertyImageCreateException
from app.storage.local import MediaSaver
from app.storage.validator import ImageValidator
from fastapi import UploadFile


class PropertyImageService:
    def __init__(
        self,
        property_image_repository: PropertyImageRepository,
        property_repository: PropertyRepository,
        media_saver: MediaSaver,
        validator: ImageValidator,
    ):
        self.property_image_repository = property_image_repository
        self.property_repository = property_repository
        self.media_saver = media_saver
        self.validator = validator

    async def add_image(
        self,
        property_id: int,
        user: UserModel,
        file: UploadFile,
    ) -> PropertyImageModel:

        property = await self.property_repository.get_by_id(property_id)

        if not property:
            raise PropertyNotFoundException("Недвижимость не найдена")

        if property.owner_id != user.id:
            raise AccessDeniedException("У вас нет прав для добавления изображения к этой недвижимости")

        await self.validator.validate(file)

        image_url = await self.media_saver.save_file(file)

        existing_images = (
            await self.property_image_repository.get_by_property_id(property_id)
        )

        if existing_images:
            position = max(image.position for image in existing_images) + 1
        else:
            position = 1

        try:
            new_image = await self.property_image_repository.add_image(
                property_id,
                image_url,
                position,
            )
            return new_image

        except Exception as e:
            await self.media_saver.delete_file(image_url)
            raise PropertyImageCreateException("Ошибка при добавлении изображения") 

    async def get_images_by_property_id(
        self,
        property_id: int,
    ) -> list[PropertyImageModel]:

        property = await self.property_repository.get_by_id(property_id)

        if not property:
            raise PropertyNotFoundException("Недвижимость не найдена")

        return await self.property_image_repository.get_by_property_id(property_id)

    async def delete_image(
        self,
        image_id: int,
        user: UserModel,
    ) -> None:

        image = await self.property_image_repository.get_by_id(image_id)

        if not image:
            raise PropertyImageNotFoundException("Изображение не найдено")

        property = await self.property_repository.get_by_id(image.property_id)

        if not property:
            raise PropertyNotFoundException("Недвижимость не найдена")

        if property.owner_id != user.id:
            raise AccessDeniedException("У вас нет прав для удаления изображения для этой недвижимости")

        await self.media_saver.delete_file(image.image_url)

        await self.property_image_repository.delete_image(image)