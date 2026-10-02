from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx_ws import WebSocketDisconnect

from app.models.bookings import Booking
from app.models.favorite import Favorite
from app.models.property_views import PropertyView
from app.db.enums import BookingStatus
from app.tests.ws import open_ws

pytestmark = pytest.mark.asyncio


def viewers_url(property_id: int, headers: dict | None = None) -> str:
    url = f"http://test/api/v1/properties/{property_id}/viewers/ws"
    if headers is not None:
        url += "?token=" + headers["Authorization"].removeprefix("Bearer ")
    return url


async def next_count(ws) -> int:
    event = await ws.receive_json()
    assert event["type"] == "viewers"
    return event["count"]


async def test_signals_aggregate_views_favorites_and_bookings(
    client, db_session, api_user, owner, owner_property,
):
    today = date.today()
    db_session.add_all([
        PropertyView(visitor_id=uuid4(), property_id=owner_property.id, view_date=today),
        PropertyView(user_id=api_user.id, property_id=owner_property.id, view_date=today),
        PropertyView(visitor_id=uuid4(), property_id=owner_property.id, view_date=today - timedelta(days=3)),
        PropertyView(visitor_id=uuid4(), property_id=owner_property.id, view_date=today - timedelta(days=10)),
        Favorite(user_id=api_user.id, property_id=owner_property.id),
        Favorite(user_id=owner.id, property_id=owner_property.id),
    ])

    def booking(status, created_days_ago):
        check_in = datetime(2031, 3, 1, tzinfo=timezone.utc) + timedelta(days=created_days_ago * 5)
        return Booking(
            property_id=owner_property.id,
            guest_id=api_user.id,
            check_in=check_in,
            check_out=check_in + timedelta(days=2),
            total_price=Decimal("200.00"),
            status=status,
            created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago),
        )

    db_session.add_all([
        booking(BookingStatus.PENDING, 0),
        booking(BookingStatus.CONFIRMED, 2),
        booking(BookingStatus.CANCELLED, 1),
        booking(BookingStatus.COMPLETED, 20),
    ])
    await db_session.flush()

    response = await client.get(f"/api/v1/properties/{owner_property.id}/signals")

    assert response.status_code == 200
    data = response.json()
    assert data["viewing_now"] == 0
    assert data["views_today"] == 2
    assert data["views_last_week"] == 3
    assert data["favorites_count"] == 2
    assert data["bookings_last_week"] == 2
    assert data["last_booked_at"] is not None


async def test_signals_for_unknown_property(client):
    response = await client.get("/api/v1/properties/999999/signals")

    assert response.status_code == 404


async def test_live_viewers_count(client, auth_headers, owner_property):
    property_id = owner_property.id

    # Подключаемся по очереди: в тестах все подключения делят одну сессию БД
    async with open_ws(viewers_url(property_id)) as anonymous:
        assert await next_count(anonymous) == 1

        async with open_ws(viewers_url(property_id, auth_headers)) as user_tab:
            assert await next_count(user_tab) == 2
            assert await next_count(anonymous) == 2

            # Вторая вкладка того же пользователя не увеличивает счетчик
            async with open_ws(viewers_url(property_id, auth_headers)) as second_tab:
                assert await next_count(second_tab) == 2
                assert await next_count(anonymous) == 2
                assert await next_count(user_tab) == 2

                signals = await client.get(f"/api/v1/properties/{property_id}/signals")
                assert signals.json()["viewing_now"] == 2

            assert await next_count(anonymous) == 2
            assert await next_count(user_tab) == 2

        assert await next_count(anonymous) == 1

    signals = await client.get(f"/api/v1/properties/{property_id}/signals")
    assert signals.json()["viewing_now"] == 0


async def test_viewers_ws_unknown_property(client):
    async with open_ws(viewers_url(999999)) as ws:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            await ws.receive_text()

    assert exc_info.value.code == 4404
