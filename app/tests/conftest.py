import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
import app.models
from app.models.users import User
from decimal import Decimal
from app.models.properties import Property


TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clickrent_test"
)


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