from app.storage.local import MediaSaver
from app.storage.validator import ImageValidator


async def get_media_saver() -> MediaSaver:
    return MediaSaver()

async def get_image_validator() -> ImageValidator:
    return ImageValidator()