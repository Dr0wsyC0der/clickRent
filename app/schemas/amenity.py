from pydantic import BaseModel, Field, ConfigDict


class AmenityCreate(BaseModel):
    name: str = Field(
        ...,
        max_length=100,
        description="Название удобства",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Описание удобства",
    )
    icon_url: str | None = Field(
        None,
        max_length=255,
        description="URL иконки удобства",
    )

class AmenityResponse(BaseModel):
    id: int = Field(
        ...,
        description="Уникальный идентификатор удобства",
    )
    name: str = Field(
        ...,
        description="Название удобства",
    )
    description: str | None = Field(
        None,
        description="Описание удобства",
    )
    icon_url: str | None = Field(
        None,
        description="URL иконки удобства",
    )

    model_config = ConfigDict(from_attributes=True)