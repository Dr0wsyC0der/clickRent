from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.db.enums import UserRole
from typing import Optional, List
from app.schemas.user import UserCreate

class RegisterRequest(UserCreate):
    role: UserRole = Field(UserRole.USER, description="Роль: user (гость) или host (владелец недвижимости)")

    @field_validator("role")
    @classmethod
    def forbid_admin_role(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError("Роль администратора нельзя выбрать при регистрации")
        return value

class LoginRequest(BaseModel):
    login: str = Field(..., description="Phone или email или username")
    password: str = Field(..., description="Пароль пользователя", min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str