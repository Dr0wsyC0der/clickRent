from datetime import datetime
from pydantic import BaseModel, Field


class PropertySignalsResponse(BaseModel):
    property_id: int = Field(..., description="ID объекта недвижимости")
    viewing_now: int = Field(..., description="Сколько пользователей смотрят объект прямо сейчас")
    views_today: int = Field(..., description="Уникальные просмотры за сегодня")
    views_last_week: int = Field(..., description="Уникальные просмотры за последние 7 дней")
    favorites_count: int = Field(..., description="Сколько пользователей добавили объект в избранное")
    bookings_last_week: int = Field(..., description="Бронирования за последние 7 дней")
    last_booked_at: datetime | None = Field(None, description="Когда объект бронировали в последний раз")
