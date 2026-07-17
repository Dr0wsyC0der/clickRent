from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional



class PropertyCreate(BaseModel):
    title: str = Field(..., description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: int = Field(..., description="Количество кроватей в объекте недвижимости")
    bathrooms: int = Field(..., description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: int = Field(..., description="Вместимость объекта недвижимости")
    rooms: int = Field(..., description="Количество комнат в объекте недвижимости")
    country: str = Field(..., description="Страна объекта недвижимости", max_length=50)
    city: str = Field(..., description="Город объекта недвижимости", max_length=50)
    address: str = Field(..., description="Адрес объекта недвижимости", max_length=100)
    price_per_night: float = Field(..., description="Цена объекта недвижимости за ночь")
    owner_id: int = Field(..., description="ID владельца объекта недвижимости")

    model_config = ConfigDict(from_attributes=True)

class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: Optional[int] = Field(None, description="Количество кроватей в объекте недвижимости")
    bathrooms: Optional[int] = Field(None, description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: Optional[int] = Field(None, description="Вместимость объекта недвижимости")
    rooms: Optional[int] = Field(None, description="Количество комнат в объекте недвижимости")
    country: Optional[str] = Field(None, description="Страна объекта недвижимости", max_length=50)
    city: Optional[str] = Field(None, description="Город объекта недвижимости", max_length=50)
    address: Optional[str] = Field(None, description="Адрес объекта недвижимости", max_length=100)
    price_per_night: Optional[float] = Field(None, description="Цена объекта недвижимости за ночь")

    model_config = ConfigDict(from_attributes=True)

class PropertyResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор объекта недвижимости")
    title: str = Field(..., description="Название объекта недвижимости", max_length=100)
    description: Optional[str] = Field(None, description="Описание объекта недвижимости")
    beds: int = Field(..., description="Количество кроватей в объекте недвижимости")
    bathrooms: int = Field(..., description="Количество ванных комнат в объекте недвижимости")
    guest_capacity: int = Field(..., description="Вместимость объекта недвижимости")
    rooms: int = Field(..., description="Количество комнат в объекте недвижимости")
    country: str = Field(..., description="Страна объекта недвижимости", max_length=50)
    city: str = Field(..., description="Город объекта недвижимости", max_length=50)
    address: str = Field(..., description="Адрес объекта недвижимости", max_length=100)
    price_per_night: float = Field(..., description="Цена объекта недвижимости за ночь")
    owner_id: int = Field(..., description="ID владельца объекта недвижимости")
    longitude: Optional[float] = Field(None, description="Долгота объекта недвижимости")
    latitude: Optional[float] = Field(None, description="Широта объекта недвижимости")
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
