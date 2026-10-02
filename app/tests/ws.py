import asyncio
import json
import os
from contextlib import asynccontextmanager

from httpx import AsyncClient
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.core.redis import create_redis
from app.main import app
from app.websocket.manager import ConnectionManager

# Отдельная логическая база Redis, которая очищается перед каждым тестом
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")


@asynccontextmanager
async def open_ws(url: str):
    """Открывает WebSocket к приложению в текущей задаче.

    Транспорт httpx-ws держит task group, поэтому его нельзя создавать в фикстуре:
    pytest-asyncio выполняет setup и teardown фикстуры в разных задачах.
    Переопределения зависимостей (тестовая сессия БД) задает фикстура `client`.
    """
    async with AsyncClient(transport=ASGIWebSocketTransport(app=app), base_url="http://test") as client:
        async with aconnect_ws(url, client) as ws:
            yield ws


class FakeWebSocket:
    """Подключение «другого инстанса»: менеджеру нужен только send_text."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.received: asyncio.Queue[dict] = asyncio.Queue()

    async def send_text(self, data: str) -> None:
        if self.fail:
            raise ConnectionError("socket is closed")
        await self.received.put(json.loads(data))

    async def next_event(self, timeout: float = 2) -> dict:
        return await asyncio.wait_for(self.received.get(), timeout)


@asynccontextmanager
async def instance_manager(namespace: str, **kwargs):
    """ConnectionManager второго инстанса приложения: собственный клиент Redis и подписка."""
    redis = create_redis(TEST_REDIS_URL)
    manager = ConnectionManager(namespace, **kwargs)
    await manager.start(redis)
    try:
        yield manager
    finally:
        await manager.stop()
        await redis.aclose()
