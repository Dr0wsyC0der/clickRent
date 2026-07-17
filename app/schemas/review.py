from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List



class CreateReview(BaseModel):
    property_id: int = Field(..., description="ID объекта недвижимости")
    booking_id: int = Field(..., description="ID бронирования")
    author_id: int = Field(..., description="ID автора отзыва")
    rating: float = Field(..., description="Рейтинг объекта недвижимости", ge=0, le=5)
    comment: Optional[str] = Field(None, description="Комментарий к отзыву")

class UpdateReview(BaseModel):
    rating: Optional[float] = Field(None, description="Рейтинг объекта недвижимости", ge=0, le=5)
    comment: Optional[str] = Field(None, description="Комментарий к отзыву")

class ReviewResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор отзыва")
    property_id: int = Field(..., description="ID объекта недвижимости")
    booking_id: int = Field(..., description="ID бронирования")
    author_id: int = Field(..., description="ID автора отзыва")
    rating: float = Field(..., description="Рейтинг объекта недвижимости", ge=0, le=5)
    comment: Optional[str] = Field(None, description="Комментарий к отзыву")
    created_at: datetime = Field(..., description="Дата создания отзыва")
    updated_at: datetime = Field(..., description="Дата последнего обновления отзыва")

    model_config = ConfigDict(from_attributes=True)

class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse] = Field(..., description="Список отзывов")
    total: int = Field(..., description="Общее количество отзывов")

    model_config = ConfigDict(from_attributes=True)