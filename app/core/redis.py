from redis.asyncio import Redis

# Общий префикс ключей и каналов приложения в Redis
KEY_PREFIX = "clickrent"

_client: Redis | None = None


def create_redis(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=True, health_check_interval=30)


def set_redis(client: Redis | None) -> None:
    """Устанавливает клиент Redis процесса (в lifespan приложения или в тестах)."""
    global _client
    _client = client


def get_redis() -> Redis:
    if _client is None:
        raise RuntimeError("Клиент Redis не инициализирован")
    return _client


def redis_key(*parts: object) -> str:
    return ":".join([KEY_PREFIX, *(str(part) for part in parts)])
