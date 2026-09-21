import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.models.users import User
from app.models.properties import Property
from app.db.enums import BookingStatus
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.services.booking import BookingService
from app.exceptions.booking import (
    BookingConflictException,
    InvalidBookingDatesException,
    BookingAccessDeniedException,
    BookingStatusException,
    BookingNotFoundException,
)


@pytest.fixture
def booking_service(db_session):
    return BookingService(
        booking_repository=BookingRepository(db_session),
        property_repository=PropertyRepository(db_session),
    )


@pytest.fixture
def booking_repository(db_session):
    return BookingRepository(db_session)


@pytest.mark.asyncio
async def test_create_booking(
    booking_service, guest, property,
):
    check_in = datetime(2026, 10, 1, tzinfo=timezone.utc)
    check_out = datetime(2026, 10, 4, tzinfo=timezone.utc)

    booking = await booking_service.create_booking(
        user_id=guest.id,
        property_id=property.id,
        check_in=check_in,
        check_out=check_out,
    )

    assert booking.id is not None
    assert booking.guest_id == guest.id
    assert booking.property_id == property.id
    assert booking.check_in == check_in
    assert booking.check_out == check_out
    assert booking.status == BookingStatus.PENDING
    assert booking.total_price == Decimal("300.00")


@pytest.mark.asyncio
async def test_create_booking_with_intersection(
    booking_service, guest, property,
):
    await booking_service.create_booking(
        user_id=guest.id,
        property_id=property.id,
        check_in=datetime(2026, 10, 1, tzinfo=timezone.utc),
        check_out=datetime(2026, 10, 4, tzinfo=timezone.utc),
    )

    with pytest.raises(BookingConflictException):
        await booking_service.create_booking(
            user_id=guest.id,
            property_id=property.id,
            check_in=datetime(2026, 10, 2, tzinfo=timezone.utc),
            check_out=datetime(2026, 10, 5, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_create_booking_with_invalid_dates(
    booking_service, guest, property,
):
    with pytest.raises(InvalidBookingDatesException):
        await booking_service.create_booking(
            user_id=guest.id,
            property_id=property.id,
            check_in=datetime(2026, 10, 5, tzinfo=timezone.utc),
            check_out=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_confirm_booking_by_owner(
    db_session, booking_service, booking_repository, guest, property,
):
    # `guest` — владелец `property`; создаём отдельного пользователя-гостя
    booker = User(
        username="test_booker",
        email="booker@test.com",
        password_hash="hashed_password",
    )
    db_session.add(booker)
    await db_session.flush()

    booking = await booking_service.create_booking(
        user_id=booker.id,
        property_id=property.id,
        check_in=datetime(2026, 11, 1, tzinfo=timezone.utc),
        check_out=datetime(2026, 11, 4, tzinfo=timezone.utc),
    )

    assert booking.status == BookingStatus.PENDING

    # Владелец подтверждает бронирование
    await booking_service.confirm_booking(
        booking_id=booking.id,
        user_id=guest.id,
    )

    confirmed_booking = await booking_repository.get_booking_by_id(booking.id)

    assert confirmed_booking is not None
    assert confirmed_booking.status == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_confirm_booking_by_not_owner(
    db_session, booking_service, booking_repository, guest, property,
):
    booker = User(
        username="test_booker_2",
        email="booker2@test.com",
        password_hash="hashed_password",
    )
    other_user = User(
        username="other_user",
        email="other@test.com",
        password_hash="hashed_password",
    )
    db_session.add_all([booker, other_user])
    await db_session.flush()

    booking = await booking_service.create_booking(
        user_id=booker.id,
        property_id=property.id,
        check_in=datetime(2026, 12, 1, tzinfo=timezone.utc),
        check_out=datetime(2026, 12, 4, tzinfo=timezone.utc),
    )

    assert booking.status == BookingStatus.PENDING

    with pytest.raises(BookingAccessDeniedException):
        await booking_service.confirm_booking(
            booking_id=booking.id,
            user_id=other_user.id,
        )

    # Статус не должен измениться
    current_booking = await booking_repository.get_booking_by_id(booking.id)

    assert current_booking is not None
    assert current_booking.status == BookingStatus.PENDING


@pytest.mark.asyncio
async def test_cancel_booking(
    booking_service, booking_repository, guest, property,
):
    booking = await booking_service.create_booking(
        user_id=guest.id,
        property_id=property.id,
        check_in=datetime(2027, 1, 1, tzinfo=timezone.utc),
        check_out=datetime(2027, 1, 4, tzinfo=timezone.utc),
    )

    assert booking.status == BookingStatus.PENDING

    await booking_service.cancel_booking(
        booking_id=booking.id,
        user_id=guest.id,
    )

    cancelled_booking = await booking_repository.get_booking_by_id(booking.id)

    assert cancelled_booking is not None
    assert cancelled_booking.status == BookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(
    booking_service, booking_repository, guest, property,
):
    booking = await booking_service.create_booking(
        user_id=guest.id,
        property_id=property.id,
        check_in=datetime(2027, 2, 1, tzinfo=timezone.utc),
        check_out=datetime(2027, 2, 4, tzinfo=timezone.utc),
    )

    # Первая отмена
    await booking_service.cancel_booking(
        booking_id=booking.id,
        user_id=guest.id,
    )

    cancelled_booking = await booking_repository.get_booking_by_id(booking.id)

    assert cancelled_booking.status == BookingStatus.CANCELLED

    # Повторная отмена должна вызвать исключение
    with pytest.raises(BookingStatusException):
        await booking_service.cancel_booking(
            booking_id=booking.id,
            user_id=guest.id,
        )


@pytest.mark.asyncio
async def test_confirm_already_confirmed_booking(
    db_session, booking_service, booking_repository, guest, property,
):
    # `guest` — владелец `property`
    booker = User(
        username="test_booker_3",
        email="booker3@test.com",
        password_hash="hashed_password",
    )
    db_session.add(booker)
    await db_session.flush()

    booking = await booking_service.create_booking(
        user_id=booker.id,
        property_id=property.id,
        check_in=datetime(2027, 3, 1, tzinfo=timezone.utc),
        check_out=datetime(2027, 3, 4, tzinfo=timezone.utc),
    )

    # Первое подтверждение
    await booking_service.confirm_booking(
        booking_id=booking.id,
        user_id=guest.id,
    )

    confirmed_booking = await booking_repository.get_booking_by_id(booking.id)

    assert confirmed_booking.status == BookingStatus.CONFIRMED

    # Повторное подтверждение
    with pytest.raises(BookingStatusException):
        await booking_service.confirm_booking(
            booking_id=booking.id,
            user_id=guest.id,
        )


@pytest.mark.asyncio
async def test_confirm_nonexistent_booking(booking_service):
    with pytest.raises(BookingNotFoundException):
        await booking_service.confirm_booking(
            booking_id=999999,
            user_id=1,
        )