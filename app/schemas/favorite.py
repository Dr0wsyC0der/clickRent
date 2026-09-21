from pydantic import BaseModel, Field
from app.schemas.property import PropertyShortResponse


class FavoriteListParams(BaseModel):
    page: int = Field(1,ge=1,description="Номер страницы")
    size: int = Field(10,ge=1,le=100,description="Количество объектов на странице")


class FavoriteListResponse(BaseModel):
    properties: list[PropertyShortResponse] = Field(...,description="Список избранных объектов недвижимости")
    total: int = Field(...,description="Общее количество избранных объектов")
    page: int = Field(...,description="Номер текущей страницы")
    size: int = Field(...,description="Количество объектов на странице")
    pages: int = Field(...,description="Общее количество страниц")