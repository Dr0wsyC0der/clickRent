import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.dependencies.redis import get_redis_client
from app.core.config import Settings, settings
from app.core import rate_limit
from app.core.rate_limit import RateLimitRule
from app.main import app

pytestmark = pytest.mark.asyncio


def login(client, password="wrong_password"):
    return client.post("/api/v1/auth/login", data={"username": "api_test_user", "password": password})


def register(client, number: int):
    return client.post("/api/v1/auth/register", json={
        "username": f"limited_user_{number}",
        "email": f"limited_user_{number}@test.com",
        "password": "limited_password",
    })


class FakeClock:
    """Окна лимитов привязаны к часам: фиксированное время исключает переход окна посреди теста."""

    def __init__(self) -> None:
        self.now = 1_800_000_000.0

    def time(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(rate_limit, "time", fake)
    return fake


@pytest.fixture
def limits(monkeypatch, clock):
    def set_limit(scope: str, value: str) -> None:
        monkeypatch.setattr(settings, f"rate_limit_{scope}", value)

    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    return set_limit


async def test_login_is_limited_per_ip(client, api_user, limits):
    limits("login", "3/minute")

    statuses = [(await login(client)).status_code for _ in range(3)]
    blocked = await login(client, password="test_password")

    assert statuses == [401, 401, 401]
    assert blocked.status_code == 429
    assert "Слишком много запросов" in blocked.json()["detail"]
    # Время зафиксировано на начале минутного окна
    assert blocked.headers["Retry-After"] == "61"


async def test_limit_is_separate_for_each_client_ip(client, api_user, limits):
    limits("login", "1/minute")
    assert (await login(client, password="test_password")).status_code == 200
    assert (await login(client, password="test_password")).status_code == 429

    other_transport = ASGITransport(app=app, client=("10.0.0.2", 40000))
    async with AsyncClient(transport=other_transport, base_url="http://test") as other_client:
        assert (await login(other_client, password="test_password")).status_code == 200


async def test_register_is_limited(client, limits):
    limits("register", "2/minute")

    statuses = [(await register(client, number)).status_code for number in range(3)]

    assert statuses == [200, 200, 429]


async def test_refresh_is_limited(client, api_user, limits):
    limits("refresh", "1/minute")
    refresh_token = (await login(client, password="test_password")).json()["refresh_token"]

    first = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    second = await client.post("/api/v1/auth/refresh", json={"refresh_token": first.json()["refresh_token"]})

    assert first.status_code == 200
    assert second.status_code == 429


async def test_scopes_are_counted_independently(client, api_user, limits):
    limits("login", "1/minute")
    await login(client)
    assert (await login(client)).status_code == 429

    assert (await register(client, 1)).status_code == 200


async def test_limit_resets_after_window(client, api_user, limits, clock):
    limits("login", "1/minute")
    assert (await login(client)).status_code == 401

    clock.now += 59
    blocked = await login(client)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "2"

    clock.now += 1
    assert (await login(client)).status_code == 401


async def test_rate_limit_can_be_disabled(client, api_user, limits, monkeypatch):
    limits("login", "1/minute")
    monkeypatch.setattr(settings, "rate_limit_enabled", False)

    statuses = [(await login(client)).status_code for _ in range(3)]

    assert statuses == [401, 401, 401]


async def test_requests_pass_when_redis_is_unavailable(client, api_user, limits):
    class BrokenRedis:
        def pipeline(self, *args, **kwargs):
            raise ConnectionError("redis is down")

    limits("login", "1/minute")
    app.dependency_overrides[get_redis_client] = lambda: BrokenRedis()

    statuses = [(await login(client)).status_code for _ in range(3)]

    assert statuses == [401, 401, 401]


async def test_counters_are_stored_with_ttl(client, api_user, limits, redis_client):
    limits("login", "5/minute")
    await login(client)

    keys = [key async for key in redis_client.scan_iter("clickrent:ratelimit:login:*")]

    assert len(keys) == 1
    assert 0 < await redis_client.ttl(keys[0]) <= 60


@pytest.mark.parametrize("value, expected", [
    ("10/minute", RateLimitRule(10, 60)),
    ("5/second", RateLimitRule(5, 1)),
    (" 100 / hour ", RateLimitRule(100, 3600)),
    ("1000/day", RateLimitRule(1000, 86400)),
    ("3/30", RateLimitRule(3, 30)),
])
async def test_parse_rate_limit_rule(value, expected):
    assert RateLimitRule.parse(value) == expected


@pytest.mark.parametrize("value", ["", "10", "ten/minute", "10/week", "0/minute", "10/0", "1/2/3"])
async def test_invalid_rate_limit_is_rejected_by_settings(value):
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+asyncpg://user:password@localhost/db",
            secret_key="secret",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=30,
            rate_limit_login=value,
        )
