from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
import pytest_asyncio

from app.models.bookings import Booking
from app.models.reviews import Review
from app.db.enums import BookingStatus
from app.security.hashing import hash_password

pytestmark = pytest.mark.asyncio

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
async def review(db_session, api_user, owner_property, completed_booking):
    review = Review(
        property_id=owner_property.id,
        booking_id=completed_booking.id,
        author_id=api_user.id,
        rating=5,
        comment="Отличная квартира",
    )
    db_session.add(review)
    await db_session.flush()

    return review


@pytest_asyncio.fixture
async def another_user(db_session):
    from app.models.users import User

    user = User(
        username="another_user",
        email="another@test.com",
        password_hash=hash_password("another_password"),
    )
    db_session.add(user)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def another_user_auth_headers(client, another_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "another_user",
            "password": "another_password",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# -------------------------
# CREATE
# -------------------------

async def test_create_review(
    client,
    auth_headers,
    completed_booking,
    owner_property,
):
    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": completed_booking.id,
            "rating": 5,
            "comment": "Отличная квартира",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["property_id"] == owner_property.id
    assert data["booking_id"] == completed_booking.id
    assert data["rating"] == 5
    assert data["comment"] == "Отличная квартира"


async def test_create_review_without_auth(
    client,
    completed_booking,
    owner_property,
):
    response = await client.post(
        "/api/v1/reviews/",
        json={
            "property_id": owner_property.id,
            "booking_id": completed_booking.id,
            "rating": 5,
            "comment": "Отличная квартира",
        },
    )

    assert response.status_code == 401


async def test_create_review_booking_not_found(
    client,
    auth_headers,
    owner_property,
):
    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": 999999,
            "rating": 5,
            "comment": "Отличная квартира",
        },
    )

    assert response.status_code == 404


async def test_create_review_for_not_completed_booking(
    client,
    auth_headers,
    db_session,
    api_user,
    owner_property,
):
    booking = Booking(
        property_id=owner_property.id,
        guest_id=api_user.id,
        check_in=datetime.now(timezone.utc) + timedelta(days=1),
        check_out=datetime.now(timezone.utc) + timedelta(days=3),
        total_price=Decimal("200.00"),
        status=BookingStatus.CONFIRMED,
    )

    db_session.add(booking)
    await db_session.flush()

    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": booking.id,
            "rating": 5,
            "comment": "Отзыв",
        },
    )

    assert response.status_code == 403


async def test_create_duplicate_review(
    client,
    auth_headers,
    review,
    completed_booking,
    owner_property,
):
    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": completed_booking.id,
            "rating": 4,
            "comment": "Второй отзыв",
        },
    )

    assert response.status_code == 409


async def test_create_review_invalid_rating(
    client,
    auth_headers,
    completed_booking,
    owner_property,
):
    response = await client.post(
        "/api/v1/reviews/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "booking_id": completed_booking.id,
            "rating": 6,
            "comment": "Отзыв",
        },
    )

    assert response.status_code == 422


# -------------------------
# GET
# -------------------------

async def test_get_review_by_id(
    client,
    review,
):
    response = await client.get(
        f"/api/v1/reviews/{review.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == review.id
    assert data["rating"] == 5
    assert data["comment"] == "Отличная квартира"


async def test_get_review_not_found(client):
    response = await client.get(
        "/api/v1/reviews/999999"
    )

    assert response.status_code == 404


async def test_get_property_reviews(
    client,
    review,
    owner_property,
):
    response = await client.get(
        f"/api/v1/reviews/property/{owner_property.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 1
    assert len(data["reviews"]) == 1


async def test_get_property_reviews_pagination(
    client,
    db_session,
    api_user,
    owner_property,
):
    for i in range(3):
        booking = Booking(
            property_id=owner_property.id,
            guest_id=api_user.id,
            check_in=datetime.now(timezone.utc) - timedelta(days=10 + i),
            check_out=datetime.now(timezone.utc) - timedelta(days=8 + i),
            total_price=Decimal("200.00"),
            status=BookingStatus.COMPLETED,
        )

        db_session.add(booking)
        await db_session.flush()

        review = Review(
            property_id=owner_property.id,
            booking_id=booking.id,
            author_id=api_user.id,
            rating=4,
            comment=f"Отзыв {i}",
        )

        db_session.add(review)

    await db_session.flush()

    response = await client.get(
        f"/api/v1/reviews/property/{owner_property.id}?page=1&size=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] == 2
    assert len(data["reviews"]) == 2


# -------------------------
# UPDATE
# -------------------------

async def test_update_review(
    client,
    auth_headers,
    review,
):
    response = await client.patch(
        f"/api/v1/reviews/{review.id}",
        headers=auth_headers,
        json={
            "rating": 4,
            "comment": "Изменённый отзыв",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["rating"] == 4
    assert data["comment"] == "Изменённый отзыв"


async def test_update_review_without_auth(
    client,
    review,
):
    response = await client.patch(
        f"/api/v1/reviews/{review.id}",
        json={
            "rating": 4,
        },
    )

    assert response.status_code == 401


async def test_update_review_other_user(
    client,
    another_user_auth_headers,
    review,
):
    response = await client.patch(
        f"/api/v1/reviews/{review.id}",
        headers=another_user_auth_headers,
        json={
            "rating": 1,
        },
    )

    assert response.status_code == 403


# -------------------------
# DELETE
# -------------------------

async def test_delete_review(
    client,
    auth_headers,
    review,
):
    response = await client.delete(
        f"/api/v1/reviews/{review.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    get_response = await client.get(
        f"/api/v1/reviews/{review.id}"
    )

    assert get_response.status_code == 404


async def test_delete_review_without_auth(
    client,
    review,
):
    response = await client.delete(
        f"/api/v1/reviews/{review.id}"
    )

    assert response.status_code == 401


async def test_delete_review_other_user(
    client,
    another_user_auth_headers,
    review,
):
    response = await client.delete(
        f"/api/v1/reviews/{review.id}",
        headers=another_user_auth_headers,
    )

    assert response.status_code == 403