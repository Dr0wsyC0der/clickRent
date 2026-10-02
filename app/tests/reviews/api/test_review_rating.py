from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.bookings import Booking
from app.models.users import User
from app.db.enums import BookingStatus
from app.security.hashing import hash_password

pytestmark = pytest.mark.asyncio


async def make_booking(db_session, guest_id, property_id, status, days_ago_check_out=2):
    booking = Booking(
        property_id=property_id,
        guest_id=guest_id,
        check_in=datetime.now(timezone.utc) - timedelta(days=days_ago_check_out + 3),
        check_out=datetime.now(timezone.utc) - timedelta(days=days_ago_check_out),
        total_price=Decimal("300.00"),
        status=status,
    )
    db_session.add(booking)
    await db_session.flush()
    return booking


@pytest_asyncio.fixture
async def second_guest_headers(client, db_session):
    user = User(
        username="second_guest",
        email="second_guest@test.com",
        password_hash=hash_password("second_password"),
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "second_guest", "password": "second_password"},
    )
    return user, {"Authorization": f"Bearer {response.json()['access_token']}"}


async def post_review(client, headers, property_id, booking_id, rating):
    return await client.post(
        "/api/v1/reviews/",
        headers=headers,
        json={"property_id": property_id, "booking_id": booking_id, "rating": rating},
    )


async def get_property(client, property_id):
    response = await client.get(f"/api/v1/properties/{property_id}")
    assert response.status_code == 200
    return response.json()


async def test_property_rating_recalculated(
    client,
    db_session,
    api_user,
    auth_headers,
    second_guest_headers,
    owner_property,
):
    second_guest, second_headers = second_guest_headers
    first_booking = await make_booking(db_session, api_user.id, owner_property.id, BookingStatus.COMPLETED)
    second_booking = await make_booking(db_session, second_guest.id, owner_property.id, BookingStatus.COMPLETED, 10)

    first = await post_review(client, auth_headers, owner_property.id, first_booking.id, 5)
    assert first.status_code == 201
    data = await get_property(client, owner_property.id)
    assert data["rating"] == 5.0
    assert data["review_count"] == 1

    second = await post_review(client, second_headers, owner_property.id, second_booking.id, 2)
    assert second.status_code == 201
    data = await get_property(client, owner_property.id)
    assert data["rating"] == 3.5
    assert data["review_count"] == 2

    update = await client.patch(
        f"/api/v1/reviews/{second.json()['id']}",
        headers=second_headers,
        json={"rating": 4},
    )
    assert update.status_code == 200
    data = await get_property(client, owner_property.id)
    assert data["rating"] == 4.5

    delete = await client.delete(f"/api/v1/reviews/{first.json()['id']}", headers=auth_headers)
    assert delete.status_code == 204
    data = await get_property(client, owner_property.id)
    assert data["rating"] == 4.0
    assert data["review_count"] == 1

    delete = await client.delete(f"/api/v1/reviews/{second.json()['id']}", headers=second_headers)
    assert delete.status_code == 204
    data = await get_property(client, owner_property.id)
    assert data["rating"] is None
    assert data["review_count"] == 0


async def test_review_allowed_for_confirmed_booking_after_check_out(
    client, db_session, api_user, auth_headers, owner_property,
):
    booking = await make_booking(db_session, api_user.id, owner_property.id, BookingStatus.CONFIRMED)

    response = await post_review(client, auth_headers, owner_property.id, booking.id, 4)

    assert response.status_code == 201


@pytest.mark.parametrize("status", [BookingStatus.CANCELLED, BookingStatus.EXPIRED, BookingStatus.PENDING])
async def test_review_forbidden_for_unfinished_stay(
    client, db_session, api_user, auth_headers, owner_property, status,
):
    booking = await make_booking(db_session, api_user.id, owner_property.id, status)

    response = await post_review(client, auth_headers, owner_property.id, booking.id, 4)

    assert response.status_code == 403


async def test_review_forbidden_for_foreign_booking(
    client, db_session, owner, auth_headers, owner_property,
):
    booking = await make_booking(db_session, owner.id, owner_property.id, BookingStatus.COMPLETED)

    response = await post_review(client, auth_headers, owner_property.id, booking.id, 4)

    assert response.status_code == 403


async def test_owner_notified_about_new_review(
    client, db_session, api_user, auth_headers, owner_auth_headers, owner_property,
):
    booking = await make_booking(db_session, api_user.id, owner_property.id, BookingStatus.COMPLETED)
    await post_review(client, auth_headers, owner_property.id, booking.id, 5)

    response = await client.get("/api/v1/notifications/", headers=owner_auth_headers)

    notifications = response.json()["notifications"]
    assert notifications[0]["type"] == "new_review"


async def test_update_review_with_null_rating(
    client, db_session, api_user, auth_headers, owner_property,
):
    booking = await make_booking(db_session, api_user.id, owner_property.id, BookingStatus.COMPLETED)
    created = await post_review(client, auth_headers, owner_property.id, booking.id, 5)

    response = await client.patch(
        f"/api/v1/reviews/{created.json()['id']}",
        headers=auth_headers,
        json={"rating": None},
    )

    assert response.status_code == 422


async def test_create_review_with_too_long_comment(
    client, db_session, api_user, auth_headers, owner_property,
):
    booking = await make_booking(db_session, api_user.id, owner_property.id, BookingStatus.COMPLETED)

    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": booking.id,
            "rating": 5,
            "comment": "a" * 501,
        },
    )

    assert response.status_code == 422
