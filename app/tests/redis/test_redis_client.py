import pytest

from app.core.redis import get_redis, redis_key, set_redis

pytestmark = pytest.mark.asyncio


async def test_redis_client_is_available(redis_client):
    assert get_redis() is redis_client
    assert await redis_client.ping() is True


async def test_redis_key_uses_application_prefix():
    assert redis_key("cache", "property", 5) == "clickrent:cache:property:5"


async def test_get_redis_without_initialization_raises(redis_client):
    set_redis(None)
    try:
        with pytest.raises(RuntimeError):
            get_redis()
    finally:
        set_redis(redis_client)


async def test_redis_ttl_for_temporary_data(redis_client):
    await redis_client.set(redis_key("test", "temp"), "value", ex=30)

    ttl = await redis_client.ttl(redis_key("test", "temp"))

    assert 0 < ttl <= 30
