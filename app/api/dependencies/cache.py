from fastapi import Depends
from redis.asyncio import Redis

from app.api.dependencies.redis import get_redis_client
from app.cache.property import PropertyCache
from app.core.config import settings


def get_property_cache(redis: Redis = Depends(get_redis_client)) -> PropertyCache:
    return PropertyCache(
        redis=redis,
        enabled=settings.cache_enabled,
        property_ttl_seconds=settings.cache_property_ttl_seconds,
        catalog_ttl_seconds=settings.cache_catalog_ttl_seconds,
    )
