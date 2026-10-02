from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from enum import Enum
from pydantic import model_validator


class PropertyCreate(BaseModel):
    title: str = Field(..., description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: int = Field(..., gt=0, description="Количество кроватей в объекте недвижимости")
    bathrooms: int = Field(..., gt=0, description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: int = Field(..., gt=0, description="Вместимость объекта недвижимости")
    rooms: int = Field(..., gt=0, description="Количество комнат в объекте недвижимости")
    country: str = Field(..., description="Страна объекта недвижимости", max_length=50)
    city: str = Field(..., description="Город объекта недвижимости", max_length=50)
    address: str = Field(..., description="Адрес объекта недвижимости", max_length=100)
    price_per_night: Decimal = Field(..., gt=0, description="Цена объекта недвижимости за ночь", max_digits=10, decimal_places=2)
    latitude: Optional[Decimal] = Field(None, gt=-90, lt=90, description="Широта объекта недвижимости")
    longitude: Optional[Decimal] = Field(None, gt=-180, lt=180, description="Долгота объекта недвижимости")
    amenity_ids: list[int] | None = Field(None, description="Список ID удобств объекта недвижимости")


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: Optional[int] = Field(None, gt=0, description="Количество кроватей в объекте недвижимости")
    bathrooms: Optional[int] = Field(None, gt=0, description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: Optional[int] = Field(None, gt=0, description="Вместимость объекта недвижимости")
    rooms: Optional[int] = Field(None, gt=0, description="Количество комнат в объекте недвижимости")
    country: Optional[str] = Field(None, description="Страна объекта недвижимости", max_length=50)
    city: Optional[str] = Field(None, description="Город объекта недвижимости", max_length=50)
    address: Optional[str] = Field(None, description="Адрес объекта недвижимости", max_length=100)
    price_per_night: Optional[Decimal] = Field(None, gt=0, description="Цена объекта недвижимости за ночь", max_digits=10, decimal_places=2)
    latitude: Optional[Decimal] = Field(None, gt=-90, lt=90, description="Широта объекта недвижимости")
    longitude: Optional[Decimal] = Field(None, gt=-180, lt=180, description="Долгота объекта недвижимости")


class PropertyResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор объекта недвижимости")
    title: str = Field(..., description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: int = Field(..., gt=0, description="Количество кроватей в объекте недвижимости")
    bathrooms: int = Field(..., gt=0, description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: int = Field(..., gt=0, description="Вместимость объекта недвижимости")
    rooms: int = Field(..., gt=0, description="Количество комнат в объекте недвижимости")
    country: str = Field(..., description="Страна объекта недвижимости", max_length=50)
    city: str = Field(..., description="Город объекта недвижимости", max_length=50)
    address: str = Field(..., description="Адрес объекта недвижимости", max_length=100)
    price_per_night: float = Field(..., gt=0, description="Цена объекта недвижимости за ночь")
    owner_id: int = Field(..., description="ID владельца объекта недвижимости")
    longitude: Optional[float] = Field(None, gt=-180, lt=180, description="Долгота объекта недвижимости")
    latitude: Optional[float] = Field(None, gt=-90, lt=90, description="Широта объекта недвижимости")
    rating: Optional[float] = Field(None, description="Рейтинг объекта недвижимости")
    review_count: int = Field(..., description="Количество отзывов объекта недвижимости")
    created_at: datetime = Field(..., description="Дата создания объекта недвижимости")
    updated_at: datetime = Field(..., description="Дата последнего обновления объекта недвижимости")

    model_config = ConfigDict(from_attributes=True)

class PropertyShortResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор объекта недвижимости")
    title: str = Field(..., description="Название объекта недвижимости", max_length=100)
    price_per_night: float = Field(..., description="Цена объекта недвижимости за ночь")
    city: str = Field(..., description="Город объекта недвижимости", max_length=50)
    country: str = Field(..., description="Страна объекта недвижимости", max_length=50)
    rating: Optional[float] = Field(None, description="Рейтинг объекта недвижимости")
    review_count: int = Field(..., description="Количество отзывов объекта недвижимости")

    model_config = ConfigDict(from_attributes=True)

class PropertyListParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(10, ge=1, le=100, description="Количество объектов недвижимости на странице")

class PropertySortBy(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING = "rating"
    POPULARITY = "popularity"
    NEWEST = "newest"

class PropertySearchParams(PropertyListParams):
    city: str | None = Field(None, description="Город объекта недвижимости", max_length=50)
    country: str | None = Field(None, description="Страна объекта недвижимости", max_length=50)
    min_price: float | None = Field(None, gt=0, description="Минимальная цена объекта недвижимости за ночь")
    max_price: float | None = Field(None, gt=0, description="Максимальная цена объекта недвижимости за ночь")
    guest_capacity: int | None = Field(None, gt=0, description="Вместимость объекта недвижимости")
    rooms: int | None = Field(None, gt=0, description="Минимальное количество комнат в объекте недвижимости")
    beds: int | None = Field(None, gt=0, description="Количество кроватей в объекте недвижимости")
    bathrooms: int | None = Field(None, gt=0, description="Количество ванных комнат в объекте недвижимости")
    rating: float | None = Field(None, ge=0, le=5, description="Рейтинг объекта недвижимости")
    check_in: datetime| None = Field(None, description="Дата заезда в формате YYYY-MM-DD")
    check_out: datetime | None = Field(None, description="Дата выезда в формате YYYY-MM-DD")
    amenity_ids: list[int] = Field(default_factory=list, description="ID удобств, которые должны быть у объекта (все сразу)")
    sort_by: PropertySortBy = Field(PropertySortBy.NEWEST, description="Сортировка: price_asc, price_desc, rating, popularity, newest")

    @model_validator(mode="after")
    def validate_dates(self):
        if (self.check_in is None) != (self.check_out is None):
            raise ValueError("Необходимо указать обе даты: check_in и check_out")

        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValueError("Дата заезда должна быть раньше даты выезда")
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("Минимальная цена не может быть больше максимальной")

        return self

class PropertySearchResponse(BaseModel):
    properties: list[PropertyShortResponse] = Field(..., description="Список объектов недвижимости")
    total: int = Field(..., description="Общее количество найденных объектов недвижимости")
    page: int = Field(..., description="Номер текущей страницы")
    size: int = Field(..., description="Количество объектов недвижимости на странице")
    pages: int = Field(..., description="Общее количество страниц")