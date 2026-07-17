from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List



class CreateBooking(BaseModel):
    property_id: int = Field(..., description="ID объекта недвижимости")
    check_in: datetime = Field(..., description="Дата начала бронирования")
    check_out: datetime = Field(..., description="Дата окончания бронирования")


class UpdateBooking(BaseModel):
    check_in: Optional[datetime] = Field(None, description="Дата начала бронирования")
    check_out: Optional[datetime] = Field(None, description="Дата окончания бронирования")


class BookingResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор бронирования")
    property_id: int = Field(..., description="ID объекта недвижимости")
    guest_id: int = Field(..., description="ID гостя")
    check_in: datetime = Field(..., description="Дата начала бронирования")
    check_out: datetime = Field(..., description="Дата окончания бронирования")
    total_price: float = Field(..., description="Общая стоимость бронирования")
    status: str = Field(..., description="Статус бронирования")
    created_at: datetime = Field(..., description="Дата создания бронирования")
    updated_at: datetime = Field(..., description="Дата последнего обновления бронирования")

    model_config = ConfigDict(from_attributes=True)

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse] = Field(..., description="Список бронирований")
    total: int = Field(..., description="Общее количество бронирований")

    model_config = ConfigDict(from_attributes=True)