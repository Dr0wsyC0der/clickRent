from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "ClickRent"
    environment: Literal["development", "production", "testing"] = "development"
    database_url: str
    secret_key: str 
    algorithm: str
    refresh_token_expire_days: int
    access_token_expire_minutes: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()