from contextlib import asynccontextmanager

from httpx import AsyncClient
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.main import app


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
