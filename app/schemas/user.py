from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional



class UserCreate(BaseModel):
    username: str = Field(..., description="Имя пользователя", max_length=50)
    email: EmailStr = Field(..., description="Email пользователя", max_length=100)
    password: str = Field(..., description="Пароль пользователя", min_length=8)
    first_name: Optional[str] = Field(None, description="Имя пользователя", max_length=50)
    last_name: Optional[str] = Field(None, description="Фамилия пользователя", max_length=50)
    phone_number: Optional[str] = Field(None, description="Номер телефона пользователя", max_length=20)

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор пользователя")
    username: str = Field(..., description="Имя пользователя", max_length=50)
    email: EmailStr = Field(..., description="Email пользователя", max_length=100)
    role: str = Field(..., description="Роль пользователя")
    is_active: bool = Field(..., description="Состояние активности пользователя")
    is_verified: bool = Field(..., description="Состояние верификации пользователя")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime = Field(..., description="Дата последнего обновления пользователя")

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, description="Имя пользователя", max_length=50)
    email: Optional[EmailStr] = Field(None, description="Email пользователя", max_length=100)
    password: Optional[str] = Field(None, description="Пароль пользователя", min_length=8)
    first_name: Optional[str] = Field(None, description="Имя пользователя", max_length=50)
    last_name: Optional[str] = Field(None, description="Фамилия пользователя", max_length=50)
    phone_number: Optional[str] = Field(None, description="Номер телефона пользователя", max_length=20)
    is_active: Optional[bool] = Field(None, description="Состояние активности пользователя")
    is_verified: Optional[bool] = Field(None, description="Состояние верификации пользователя")
    role: Optional[str] = Field(None, description="Роль пользователя")

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя", max_length=100)
    password: str = Field(..., description="Пароль пользователя", min_length=8)

    model_config = ConfigDict(from_attributes=True)