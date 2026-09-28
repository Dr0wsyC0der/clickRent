import pytest
import pytest_asyncio

from app.db.enums import NotificationType
from app.models.notifications import Notification


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def notification(db_session, api_user):
    notification = Notification(
        user_id=api_user.id,
        type=NotificationType.BOOKING_CREATED,
        title="Новое бронирование",
        message="Пользователь создал новое бронирование.",
    )

    db_session.add(notification)
    await db_session.flush()

    return notification


@pytest_asyncio.fixture
async def notification_2(db_session, api_user):
    notification = Notification(
        user_id=api_user.id,
        type=NotificationType.NEW_REVIEW,
        title="Новый отзыв",
        message="У вас появился новый отзыв.",
    )

    db_session.add(notification)
    await db_session.flush()

    return notification


@pytest_asyncio.fixture
async def another_user(db_session):
    from app.models.users import User
    from app.security.hashing import hash_password

    user = User(
        username="notification_other_user",
        email="notification_other@test.com",
        password_hash=hash_password("notification_password"),
    )

    db_session.add(user)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def another_user_auth_headers(client, another_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "notification_other_user",
            "password": "notification_password",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


# =========================
# GET LIST
# =========================

async def test_get_notifications_empty(
    client,
    auth_headers,
):
    response = await client.get(
        "/api/v1/notifications/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["notifications"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 0


async def test_get_notifications(
    client,
    auth_headers,
    notification,
):
    response = await client.get(
        "/api/v1/notifications/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["notifications"]) == 1

    item = data["notifications"][0]

    assert item["id"] == notification.id
    assert item["user_id"] == notification.user_id
    assert item["type"] == "booking_created"
    assert item["title"] == "Новое бронирование"
    assert item["message"] == "Пользователь создал новое бронирование."
    assert item["is_read"] is False


async def test_get_notifications_without_auth(
    client,
):
    response = await client.get(
        "/api/v1/notifications/",
    )

    assert response.status_code == 401


# =========================
# PAGINATION
# =========================

async def test_get_notifications_pagination(
    client,
    auth_headers,
    notification,
    notification_2,
):
    response = await client.get(
        "/api/v1/notifications/?page=1&size=1",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 1
    assert data["pages"] == 2
    assert len(data["notifications"]) == 1


# =========================
# GET BY ID
# =========================

async def test_get_notification(
    client,
    auth_headers,
    notification,
):
    response = await client.get(
        f"/api/v1/notifications/{notification.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification.id
    assert data["type"] == "booking_created"
    assert data["is_read"] is False


async def test_get_notification_without_auth(
    client,
    notification,
):
    response = await client.get(
        f"/api/v1/notifications/{notification.id}",
    )

    assert response.status_code == 401


async def test_get_notification_not_found(
    client,
    auth_headers,
):
    response = await client.get(
        "/api/v1/notifications/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_get_notification_other_user(
    client,
    another_user_auth_headers,
    notification,
):
    response = await client.get(
        f"/api/v1/notifications/{notification.id}",
        headers=another_user_auth_headers,
    )

    assert response.status_code == 404


# =========================
# MARK AS READ
# =========================

async def test_mark_notification_as_read(
    client,
    auth_headers,
    notification,
):
    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification.id
    assert data["is_read"] is True


async def test_mark_notification_as_read_without_auth(
    client,
    notification,
):
    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
    )

    assert response.status_code == 401


async def test_mark_notification_as_read_other_user(
    client,
    another_user_auth_headers,
    notification,
):
    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=another_user_auth_headers,
    )

    assert response.status_code == 404


# =========================
# MARK ALL AS READ
# =========================

async def test_mark_all_notifications_as_read(
    client,
    auth_headers,
    notification,
    notification_2,
):
    response = await client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        "/api/v1/notifications/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["notifications"]) == 2

    for item in data["notifications"]:
        assert item["is_read"] is True


async def test_mark_all_notifications_as_read_without_auth(
    client,
):
    response = await client.patch(
        "/api/v1/notifications/read-all",
    )

    assert response.status_code == 401


# =========================
# DELETE
# =========================

async def test_delete_notification(
    client,
    auth_headers,
    notification,
):
    response = await client.delete(
        f"/api/v1/notifications/{notification.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/notifications/{notification.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_delete_notification_without_auth(
    client,
    notification,
):
    response = await client.delete(
        f"/api/v1/notifications/{notification.id}",
    )

    assert response.status_code == 401


async def test_delete_notification_other_user(
    client,
    another_user_auth_headers,
    notification,
):
    response = await client.delete(
        f"/api/v1/notifications/{notification.id}",
        headers=another_user_auth_headers,
    )

    assert response.status_code == 404