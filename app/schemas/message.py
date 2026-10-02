from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Текст сообщения")

    model_config = ConfigDict(str_strip_whitespace=True)


class MessageResponse(BaseModel):
    id: int = Field(..., description="ID сообщения")
    chat_id: int = Field(..., description="ID чата")
    sender_id: int = Field(..., description="ID отправителя")
    content: str = Field(..., description="Текст сообщения")
    created_at: datetime = Field(..., description="Дата отправки сообщения")

    model_config = ConfigDict(from_attributes=True)


class MessageListParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(50, ge=1, le=100, description="Количество сообщений на странице")


class MessageListResponse(BaseModel):
    messages: list[MessageResponse] = Field(..., description="Сообщения, от новых к старым")
    total: int = Field(..., description="Общее количество сообщений")
    page: int = Field(..., description="Номер текущей страницы")
    size: int = Field(..., description="Количество сообщений на странице")
    pages: int = Field(..., description="Общее количество страниц")
