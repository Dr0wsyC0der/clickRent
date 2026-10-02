import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.redis import create_redis
from app.db.enums import BookingStatus, NotificationType
from app.models.bookings import Booking
from app.models.notifications import Notification
from app.models.users import User
from app.tasks import booking as booking_tasks
from app.tasks.booking import MAINTENANCE_LOCK_KEY, acquire_maintenance_slot, process_bookings
from app.tests.ws import TEST_REDIS_URL

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def worker_redis_clients():
    """Отдельные клиенты Redis — как у разных воркеров и инстансов."""
    clients = [create_redis(TEST_REDIS_URL) for _ in range(4)]
    yield clients
    for client in clients:
        await client.aclose()


async def test_maintenance_slot_is_acquired_once_per_period(redis_client):
    assert await acquire_maintenance_slot(redis_client, 60) is True
    assert await acquire_maintenance_slot(redis_client, 60) is False
    assert 0 < await redis_client.ttl(MAINTENANCE_LOCK_KEY) <= 60


async def test_only_one_worker_acquires_maintenance_slot(worker_redis_clients):
    results = await asyncio.gather(*(acquire_maintenance_slot(client, 60) for client in worker_redis_clients))

    assert results.count(True) == 1


async def test_maintenance_runs_without_redis():
    class BrokenRedis:
        async def set(self, *args, **kwargs):
            raise ConnectionError("redis is down")

    assert await acquire_maintenance_slot(BrokenRedis(), 60) is True


async def test_maintenance_loops_of_several_workers_process_once(monkeypatch, worker_redis_clients):
    calls = []

    async def fake_process_bookings(session_maker):
        calls.append(session_maker)
        return 0, 0

    monkeypatch.setattr(booking_tasks, "process_bookings", fake_process_bookings)

    loops = [
        asyncio.create_task(booking_tasks.run_booking_maintenance(object(), client, interval_seconds=60))
        for client in worker_redis_clients
    ]
    await asyncio.sleep(0.5)
    for loop in loops:
        loop.cancel()
    await asyncio.gather(*loops, return_exceptions=True)

    assert len(calls) == 1


async def test_parallel_processing_does_not_duplicate_transitions(test_engine, db_session, property):
    """Даже без лока (Redis недоступен) параллельные запуски не дублируют переходы и уведомления."""
    booker = User(username="task_booker", email="task_booker@test.com", password_hash="hashed_password")
    db_session.add(booker)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Booking(
            property_id=property.id, guest_id=booker.id,
            check_in=now + timedelta(days=5), check_out=now + timedelta(days=7),
            total_price=Decimal("200.00"), status=BookingStatus.PENDING,
            expires_at=now - timedelta(minutes=1),
        ),
        Booking(
            property_id=property.id, guest_id=booker.id,
            check_in=now - timedelta(days=5), check_out=now - timedelta(days=2),
            total_price=Decimal("300.00"), status=BookingStatus.CONFIRMED,
        ),
    ])
    await db_session.commit()

    session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)
    results = await asyncio.gather(*(process_bookings(session_maker) for _ in range(3)))

    assert sum(expired for expired, _ in results) == 1
    assert sum(completed for _, completed in results) == 1

    notification_types = sorted(
        notification.type.value
        for notification in (await db_session.scalars(
            select(Notification).where(Notification.user_id == booker.id)
        )).all()
    )
    assert notification_types == sorted([
        NotificationType.BOOKING_EXPIRED.value,
        NotificationType.BOOKING_COMPLETED.value,
    ])
