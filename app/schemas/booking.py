from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional

from app.db.enums import BookingStatus


class CreateBooking(BaseModel):
    property_id: int = Field(..., description="ID объекта недвижимости")
    check_in: datetime = Field(..., description="Дата начала бронирования")
    check_out: datetime = Field(..., description="Дата окончания бронирования")
    guests: int = Field(1, ge=1, description="Количество гостей")

    @field_validator("check_in", "check_out")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        # Даты без часового пояса считаем UTC, чтобы их можно было сравнивать с текущим временем
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class UpdateBooking(BaseModel):
    check_in: Optional[datetime] = Field(None, description="Дата начала бронирования")
    check_out: Optional[datetime] = Field(None, description="Дата окончания бронирования")


class BookingResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор бронирования")
    property_id: int = Field(..., description="ID объекта недвижимости")
    guest_id: int = Field(..., description="ID гостя")
    check_in: datetime = Field(..., description="Дата начала бронирования")
    check_out: datetime  = Field(..., description="Дата окончания бронирования")
    guests: int = Field(..., description="Количество гостей")
    total_price: float = Field(..., description="Общая стоимость бронирования")
    status: str = Field(..., description="Статус бронирования")
    expires_at: Optional[datetime] = Field(None, description="Срок, до которого владелец должен подтвердить бронирование")
    created_at: datetime = Field(..., description="Дата создания бронирования")
    updated_at: datetime = Field(..., description="Дата последнего обновления бронирования")

    model_config = ConfigDict(from_attributes=True)

class BookingListParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field( 10, ge=1, le=100, description="Количество бронирований на странице")

class HostBookingListParams(BookingListParams):
    status: BookingStatus | None = Field(None, description="Фильтр по статусу бронирования")

class BookingListResponse(BaseModel):
    bookings: list[BookingResponse] = Field(...,description="Список бронирований")
    total: int = Field(...,description="Общее количество бронирований")
    page: int = Field(...,description="Номер текущей страницы")
    size: int = Field(...,description="Количество бронирований на странице")
    pages: int = Field(...,description="Общее количество страниц")
