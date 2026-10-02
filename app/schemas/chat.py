from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.message import MessageResponse


class ChatCreate(BaseModel):
    participant_id: int = Field(..., description="ID пользователя, с которым нужно открыть чат")


class ChatResponse(BaseModel):
    id: int = Field(..., description="ID чата")
    participant_ids: list[int] = Field(..., description="ID участников чата")
    last_message: MessageResponse | None = Field(None, description="Последнее сообщение")
    created_at: datetime = Field(..., description="Дата создания чата")
    updated_at: datetime = Field(..., description="Дата последней активности в чате")


class ChatListParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(20, ge=1, le=100, description="Количество чатов на странице")


class ChatListResponse(BaseModel):
    chats: list[ChatResponse] = Field(..., description="Чаты пользователя, от недавних к старым")
    total: int = Field(..., description="Общее количество чатов")
    page: int = Field(..., description="Номер текущей страницы")
    size: int = Field(..., description="Количество чатов на странице")
    pages: int = Field(..., description="Общее количество страниц")
