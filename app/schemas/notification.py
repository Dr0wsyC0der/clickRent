from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.db.enums import NotificationType


class NotificationResponse(BaseModel):
    id: int = Field(..., description="ID уведомления")
    user_id: int = Field(..., description="ID пользователя, которому принадлежит уведомление")
    type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., max_length=100, description="Заголовок уведомления")
    message: str = Field(..., max_length=255, description="Текст уведомления")
    is_read: bool = Field(..., description="Прочитано ли уведомление")
    created_at: datetime = Field(..., description="Дата и время создания уведомления")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления уведомления")

    model_config = ConfigDict(from_attributes=True)


class NotificationListParams(BaseModel):
    page: int = Field(1,ge=1,description="Номер страницы")
    size: int = Field(10,ge=1,le=100,description="Количество уведомлений на странице")


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse] = Field(...,description="Список уведомлений")
    total: int = Field(...,ge=0,description="Общее количество уведомлений")
    page: int = Field(...,ge=1,description="Текущая страница")
    size: int = Field(...,ge=1,le=100,description="Количество уведомлений на странице")
    pages: int = Field(...,ge=0,description="Общее количество страниц")