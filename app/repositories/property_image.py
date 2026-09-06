from sqlalchemy import select
from app.models.property_images import PropertyImage as PropertyImageModel
from app.repositories.base import BaseRepository



class PropertyImageRepository(BaseRepository):
    async def add_image(self, property_id: int, image_url: str, position: int) -> PropertyImageModel:
        new_image = PropertyImageModel(property_id=property_id, image_url=image_url, position=position)
        self.session.add(new_image)
        await self.session.commit()
        return new_image

    async def get_by_id(self, image_id: int) -> PropertyImageModel | None:
        result = await self.session.scalars(select(PropertyImageModel).where(PropertyImageModel.id == image_id))
        return result.first()

    async def get_by_property_id(self, property_id: int) -> list[PropertyImageModel]:
        result = await self.session.scalars(select(PropertyImageModel).where(PropertyImageModel.property_id == property_id).order_by(PropertyImageModel.position))
        return list(result)

    async def delete_image(self, image: PropertyImageModel) -> None:
        await self.session.delete(image)
        await self.session.commit()