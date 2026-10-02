from redis.asyncio import Redis

from app.core.redis import get_redis


def get_redis_client() -> Redis:
    return get_redis()
