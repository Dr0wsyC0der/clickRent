from fastapi import Depends
from app.repositories.property_image import PropertyImageRepository
from app.repositories.property import PropertyRepository
from app.services.property_image import PropertyImageService
from app.storage.local import MediaSaver
from app.storage.validator import ImageValidator
from app.api.dependencies.repositories import get_property_image_repository, get_property_repository
from app.api.dependencies.media import get_media_saver, get_image_validator

async def get_property_image_service(
    property_image_repository: PropertyImageRepository = Depends(get_property_image_repository),
    property_repository: PropertyRepository = Depends(get_property_repository),
    media_saver: MediaSaver = Depends(get_media_saver),
    validator: ImageValidator = Depends(get_image_validator),
) -> PropertyImageService:
    return PropertyImageService(
        property_image_repository=property_image_repository,
        property_repository=property_repository,
        media_saver=media_saver,
        validator=validator,
    )