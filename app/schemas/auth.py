from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.schemas.user import UserCreate

class RegisterRequest(UserCreate):
    pass

class LoginRequest(BaseModel):
    login: str = Field(..., description="Phone или email или username")
    password: str = Field(..., description="Пароль пользователя", min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str