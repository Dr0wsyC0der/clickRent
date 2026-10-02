from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "ClickRent"
    environment: Literal["development", "production", "testing"] = "development"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    algorithm: str
    refresh_token_expire_days: int
    access_token_expire_minutes: int
    booking_pending_ttl_minutes: int = 30
    booking_tasks_interval_seconds: int = 60
    # Присутствие WebSocket-подключений в Redis: TTL записи и период ее продления
    ws_presence_ttl_seconds: int = 60
    ws_heartbeat_interval_seconds: int = 20
    # Rate limiting чувствительных эндпоинтов: "<количество>/<second|minute|hour|day>" с одного IP
    rate_limit_enabled: bool = True
    rate_limit_login: str = "10/minute"
    rate_limit_register: str = "5/minute"
    rate_limit_refresh: str = "30/minute"
    log_level: str = "INFO"
    sql_echo: bool = False

    # extra="ignore": в .env лежат и переменные docker compose (POSTGRES_*, HTTP_PORT, ...)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("rate_limit_login", "rate_limit_register", "rate_limit_refresh")
    @classmethod
    def validate_rate_limit(cls, value: str) -> str:
        # Ошибка в формате лимита обнаруживается при старте, а не на первом запросе
        from app.core.rate_limit import RateLimitRule

        RateLimitRule.parse(value)
        return value

settings = Settings()