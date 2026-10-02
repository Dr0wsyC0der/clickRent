import os
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.db.enums import UserRole
from app.security.hashing import hash_password
from app.db.base import Base
from app.models.users import User
from decimal import Decimal
from app.models.properties import Property
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.dependencies.db import get_session
from datetime import datetime, timedelta, timezone
from app.models.bookings import Booking
from app.db.enums import BookingStatus
from app.core.redis import create_redis, set_redis
from app.websocket.manager import chat_manager, property_viewers_manager


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clickrent_test",
)
from app.tests.ws import TEST_REDIS_URL


@pytest_asyncio.fixture(autouse=True)
async def redis_client():
    # Клиент создается на каждый тест: соединения redis.asyncio привязаны к event loop теста
    client = create_redis(TEST_REDIS_URL)
    await client.flushdb()
    set_redis(client)

    yield client

    set_redis(None)
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def websocket_managers(redis_client):
    # Lifespan приложения в тестах не выполняется, поэтому менеджеры запускаются здесь
    managers = (chat_manager, property_viewers_manager)
    for manager in managers:
        await manager.start(redis_client)

    yield managers

    for manager in managers:
        await manager.stop()


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_maker = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_headers(client, api_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }

@pytest_asyncio.fixture
async def guest(db_session):
    user = User(
        username="test_guest",
        email="guest@test.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    await db_session.flush()

    return user

@pytest_asyncio.fixture
async def property(db_session, guest):
    property = Property(
        owner_id=guest.id,
        title="Test apartment",
        description="Test description",
        price_per_night=Decimal("100.00"),
        country="Russia",
        city="Moscow",
        address="Test street, 1",
        rooms=2,
        beds=2,
        bathrooms=1,
        guest_capacity=4,
    )

    db_session.add(property)
    await db_session.flush()

    return property

@pytest_asyncio.fixture
async def api_user(db_session):
    user = User(
        username="api_test_user",
        email="api_test@test.com",
        password_hash=hash_password("test_password"),
    )

    db_session.add(user)
    await db_session.flush()

    return user

@pytest_asyncio.fixture
async def owner(db_session):
    user = User(
        username="api_owner",
        email="api_owner@test.com",
        password_hash=hash_password("owner_password"),
        role=UserRole.HOST,
    )

    db_session.add(user)
    await db_session.flush()

    return user

@pytest_asyncio.fixture
async def owner_property(db_session, owner):
    property = Property(
        owner_id=owner.id,
        title="Owner apartment",
        description="Owner test apartment",
        price_per_night=Decimal("100.00"),
        country="Russia",
        city="Moscow",
        address="Owner street, 1",
        rooms=2,
        beds=2,
        bathrooms=1,
        guest_capacity=4,
    )

    db_session.add(property)
    await db_session.flush()

    return property

@pytest_asyncio.fixture
async def completed_booking(db_session, api_user, owner_property):
    booking = Booking(
        property_id=owner_property.id,
        guest_id=api_user.id,
        check_in=datetime.now(timezone.utc) - timedelta(days=5),
        check_out=datetime.now(timezone.utc) - timedelta(days=2),
        total_price=Decimal("300.00"),
        status=BookingStatus.COMPLETED,
    )
    db_session.add(booking)
    await db_session.flush()
    return booking

@pytest_asyncio.fixture
async def owner_auth_headers(client, owner):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_owner",
            "password": "owner_password",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }