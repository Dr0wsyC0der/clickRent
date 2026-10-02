import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.users import User
from app.models.bookings import Booking
from app.models.notifications import Notification
from app.db.enums import BookingStatus, NotificationType
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.notification import NotificationRepository
from app.services.booking import BookingService
from app.services.notification import NotificationService
from app.exceptions.booking import (
    BookingConflictException,
    InvalidBookingDatesException,
    BookingCapacityException,
    BookingStatusException,
)

pytestmark = pytest.mark.asyncio


def build_booking_service(session: AsyncSession) -> BookingService:
    return BookingService(
        booking_repository=BookingRepository(session),
        property_repository=PropertyRepository(session),
        notification_service=NotificationService(NotificationRepository(session)),
    )


@pytest.fixture
def booking_service(db_session):
    return build_booking_service(db_session)


@pytest_asyncio.fixture
async def booker(db_session):
    user = User(
        username="lifecycle_booker",
        email="lifecycle_booker@test.com",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.flush()
    return user


def future(days: int) -> datetime:
    base = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    return base + timedelta(days=days)


async def add_booking(db_session, property, guest_id, check_in, check_out, status, expires_at=None):
    booking = Booking(
        property_id=property.id,
        guest_id=guest_id,
        check_in=check_in,
        check_out=check_out,
        total_price=Decimal("100.00"),
        status=status,
        expires_at=expires_at,
    )
    db_session.add(booking)
    await db_session.flush()
    return booking


async def test_create_booking_sets_soft_lock(booking_service, booker, property):
    booking = await booking_service.create_booking(
        user_id=booker.id,
        property_id=property.id,
        check_in=future(10),
        check_out=future(12),
        guests=2,
    )

    assert booking.status == BookingStatus.PENDING
    assert booking.guests == 2
    assert booking.expires_at is not None
    assert booking.expires_at > datetime.now(timezone.utc)
    assert booking.total_price == Decimal("200.00")


async def test_create_booking_in_past(booking_service, booker, property):
    with pytest.raises(InvalidBookingDatesException):
        await booking_service.create_booking(
            user_id=booker.id,
            property_id=property.id,
            check_in=future(-3),
            check_out=future(-1),
        )


async def test_create_booking_shorter_than_one_night(booking_service, booker, property):
    check_in = future(5)
    with pytest.raises(InvalidBookingDatesException):
        await booking_service.create_booking(
            user_id=booker.id,
            property_id=property.id,
            check_in=check_in,
            check_out=check_in + timedelta(hours=5),
        )


async def test_create_booking_over_capacity(booking_service, booker, property):
    with pytest.raises(BookingCapacityException):
        await booking_service.create_booking(
            user_id=booker.id,
            property_id=property.id,
            check_in=future(5),
            check_out=future(7),
            guests=property.guest_capacity + 1,
        )


async def test_adjacent_bookings_do_not_conflict(booking_service, booker, property):
    await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(5), check_out=future(7),
    )

    booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(7), check_out=future(9),
    )

    assert booking.id is not None


async def test_expired_pending_booking_does_not_block_dates(db_session, booking_service, booker, property):
    await add_booking(
        db_session, property, booker.id, future(5), future(8),
        BookingStatus.PENDING, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(6), check_out=future(7),
    )

    assert booking.status == BookingStatus.PENDING


async def test_active_pending_booking_blocks_dates(db_session, booking_service, booker, property):
    await add_booking(
        db_session, property, booker.id, future(5), future(8),
        BookingStatus.PENDING, expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )

    with pytest.raises(BookingConflictException):
        await booking_service.create_booking(
            user_id=booker.id, property_id=property.id, check_in=future(6), check_out=future(7),
        )


async def test_cancelled_booking_frees_dates(booking_service, booker, property):
    booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(5), check_out=future(8),
    )
    await booking_service.cancel_booking(booking.id, booker.id)

    new_booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(5), check_out=future(8),
    )

    assert new_booking.status == BookingStatus.PENDING


async def test_confirm_expired_booking(db_session, booking_service, booker, guest, property):
    booking = await add_booking(
        db_session, property, booker.id, future(5), future(8),
        BookingStatus.PENDING, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    with pytest.raises(BookingStatusException):
        await booking_service.confirm_booking(booking_id=booking.id, user_id=guest.id)


async def test_expire_pending_bookings(db_session, booking_service, booker, property):
    expired = await add_booking(
        db_session, property, booker.id, future(5), future(8),
        BookingStatus.PENDING, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    active = await add_booking(
        db_session, property, booker.id, future(10), future(12),
        BookingStatus.PENDING, expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )

    count = await booking_service.expire_pending_bookings()

    assert count == 1
    assert (await db_session.get(Booking, expired.id, populate_existing=True)).status == BookingStatus.EXPIRED
    assert (await db_session.get(Booking, active.id, populate_existing=True)).status == BookingStatus.PENDING

    notifications = (await db_session.scalars(
        select(Notification).where(Notification.user_id == booker.id)
    )).all()
    assert [n.type for n in notifications] == [NotificationType.BOOKING_EXPIRED]


async def test_complete_finished_bookings(db_session, booking_service, booker, property):
    finished = await add_booking(
        db_session, property, booker.id, future(-5), future(-2), BookingStatus.CONFIRMED,
    )
    upcoming = await add_booking(
        db_session, property, booker.id, future(3), future(5), BookingStatus.CONFIRMED,
    )

    count = await booking_service.complete_finished_bookings()

    assert count == 1
    assert (await db_session.get(Booking, finished.id, populate_existing=True)).status == BookingStatus.COMPLETED
    assert (await db_session.get(Booking, upcoming.id, populate_existing=True)).status == BookingStatus.CONFIRMED

    notification = (await db_session.scalars(
        select(Notification).where(Notification.user_id == booker.id)
    )).first()
    assert notification.type == NotificationType.BOOKING_COMPLETED


async def test_owner_can_reject_booking(db_session, booking_service, booker, guest, property):
    # `guest` — владелец `property`
    booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(5), check_out=future(8),
    )

    await booking_service.cancel_booking(booking_id=booking.id, user_id=guest.id)

    cancelled = await db_session.get(Booking, booking.id, populate_existing=True)
    assert cancelled.status == BookingStatus.CANCELLED

    notification = (await db_session.scalars(
        select(Notification).where(Notification.user_id == booker.id)
    )).first()
    assert notification.type == NotificationType.BOOKING_CANCELLED
    assert notification.title == "Бронирование отклонено"


async def test_cannot_cancel_confirmed_booking_after_check_in(db_session, booking_service, booker, property):
    booking = await add_booking(
        db_session, property, booker.id, future(-1), future(2), BookingStatus.CONFIRMED,
    )

    with pytest.raises(BookingStatusException):
        await booking_service.cancel_booking(booking_id=booking.id, user_id=booker.id)


async def test_owner_can_view_booking(booking_service, booker, guest, property):
    booking = await booking_service.create_booking(
        user_id=booker.id, property_id=property.id, check_in=future(5), check_out=future(8),
    )

    found = await booking_service.get_booking_by_id(booking_id=booking.id, user_id=guest.id)

    assert found.id == booking.id


async def test_concurrent_bookings_only_one_succeeds(test_engine, db_session, booker, property):
    # Данные фикстур должны быть видны другим соединениям
    await db_session.commit()
    session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)
    check_in, check_out = future(20), future(23)
    attempts = 5
    barrier = asyncio.Barrier(attempts)

    async def attempt() -> str:
        async with session_maker() as session:
            # Заранее открываем соединения и стартуем одновременно, чтобы запросы реально пересеклись
            await session.execute(text("SELECT 1"))
            await barrier.wait()
            service = build_booking_service(session)
            try:
                await service.create_booking(
                    user_id=booker.id, property_id=property.id, check_in=check_in, check_out=check_out,
                )
                return "created"
            except BookingConflictException:
                return "conflict"

    results = await asyncio.gather(*(attempt() for _ in range(attempts)))

    assert results.count("created") == 1
    assert results.count("conflict") == attempts - 1

    bookings = (await db_session.scalars(
        select(Booking).where(Booking.property_id == property.id)
    )).all()
    assert len(bookings) == 1
