from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PropertyImageResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор изображения")
    property_id: int = Field(..., description="ID объекта недвижимости")
    image_url: str = Field(..., description="URL изображения")
    position: int = Field(..., description="Позиция изображения")
    created_at: datetime = Field(..., description="Дата создания изображения")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("image_url")
    @classmethod
    def build_image_url(cls, value: str) -> str:
        return f"/media/{value}"
