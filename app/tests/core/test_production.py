import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.api.dependencies.db import get_session
from app.api.dependencies.property import get_property_service

pytestmark = pytest.mark.asyncio


async def test_liveness(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_readiness_with_database(client):
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_readiness_without_database(client):
    class BrokenSession:
        async def execute(self, *args, **kwargs):
            raise ConnectionError("database is down")

    async def broken_session():
        yield BrokenSession()

    app.dependency_overrides[get_session] = broken_session

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


async def test_request_id_header(client):
    generated = await client.get("/health")
    forwarded = await client.get("/health", headers={"X-Request-ID": "trace-123"})

    assert generated.headers["X-Request-ID"]
    assert forwarded.headers["X-Request-ID"] == "trace-123"


async def test_unhandled_error_returns_json_500(client):
    async def failing_service():
        raise RuntimeError("неожиданная ошибка")

    app.dependency_overrides[get_property_service] = failing_service

    # raise_app_exceptions=False: проверяем ответ клиенту, а не исключение внутри транспорта
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as raw_client:
        response = await raw_client.get("/api/v1/properties/1")

    assert response.status_code == 500
    assert response.json() == {"detail": "Внутренняя ошибка сервера."}


async def test_integrity_error_returns_409(client):
    async def conflicting_service():
        raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    app.dependency_overrides[get_property_service] = conflicting_service

    response = await client.get("/api/v1/properties/1")

    assert response.status_code == 409
    assert response.json()["detail"]
