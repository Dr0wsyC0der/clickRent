import pytest
import pytest_asyncio

from app.db.enums import UserRole
from app.models.users import User
from app.security.hashing import hash_password

pytestmark = pytest.mark.asyncio

PROPERTY_PAYLOAD = {
    "title": "Права доступа",
    "beds": 1,
    "bathrooms": 1,
    "guest_capacity": 2,
    "rooms": 1,
    "country": "Russia",
    "city": "Kazan",
    "address": "Permission street, 1",
    "price_per_night": "80.00",
}


@pytest_asyncio.fixture
async def admin_headers(client, db_session):
    db_session.add(User(
        username="api_admin",
        email="api_admin@test.com",
        password_hash=hash_password("admin_password"),
        role=UserRole.ADMIN,
    ))
    await db_session.flush()

    response = await client.post("/api/v1/auth/login", data={"username": "api_admin", "password": "admin_password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def other_host_headers(client, db_session):
    db_session.add(User(
        username="other_host",
        email="other_host@test.com",
        password_hash=hash_password("host_password"),
        role=UserRole.HOST,
    ))
    await db_session.flush()

    response = await client.post("/api/v1/auth/login", data={"username": "other_host", "password": "host_password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_all_bookings_admin_only(client, auth_headers, owner_auth_headers, admin_headers):
    assert (await client.get("/api/v1/bookings/")).status_code == 401
    assert (await client.get("/api/v1/bookings/", headers=auth_headers)).status_code == 403
    assert (await client.get("/api/v1/bookings/", headers=owner_auth_headers)).status_code == 403
    assert (await client.get("/api/v1/bookings/", headers=admin_headers)).status_code == 200


@pytest.mark.parametrize("method, path", [
    ("post", "/api/v1/properties/"),
    ("get", "/api/v1/properties/host"),
    ("get", "/api/v1/bookings/host"),
])
async def test_host_only_endpoints_forbidden_for_user_and_admin(client, auth_headers, admin_headers, method, path):
    kwargs = {"json": PROPERTY_PAYLOAD} if method == "post" else {}

    user_response = await getattr(client, method)(path, headers=auth_headers, **kwargs)
    admin_response = await getattr(client, method)(path, headers=admin_headers, **kwargs)

    assert user_response.status_code == 403
    assert admin_response.status_code == 403
    assert user_response.json()["detail"]


async def test_host_cannot_manage_foreign_property(client, other_host_headers, owner_property):
    property_id = owner_property.id

    update = await client.patch(f"/api/v1/properties/{property_id}", headers=other_host_headers, json={"title": "Чужое"})
    delete = await client.delete(f"/api/v1/properties/{property_id}", headers=other_host_headers)
    amenity = await client.delete(f"/api/v1/properties/{property_id}/amenities/1", headers=other_host_headers)

    assert update.status_code == 403
    assert delete.status_code == 403
    assert amenity.status_code in (403, 404)


async def test_host_cannot_confirm_or_see_foreign_bookings(client, auth_headers, other_host_headers, owner_property):
    booking = await client.post("/api/v1/bookings/", headers=auth_headers, json={
        "property_id": owner_property.id,
        "check_in": "2032-01-01T00:00:00Z",
        "check_out": "2032-01-03T00:00:00Z",
    })
    booking_id = booking.json()["id"]

    assert (await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=other_host_headers)).status_code == 403
    assert (await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=other_host_headers)).status_code == 403
    assert (await client.get(f"/api/v1/bookings/{booking_id}", headers=other_host_headers)).status_code == 403
    assert (await client.get("/api/v1/bookings/host", headers=other_host_headers)).json()["total"] == 0


async def test_guest_cannot_confirm_own_booking(client, auth_headers, owner_property):
    booking = await client.post("/api/v1/bookings/", headers=auth_headers, json={
        "property_id": owner_property.id,
        "check_in": "2032-02-01T00:00:00Z",
        "check_out": "2032-02-03T00:00:00Z",
    })

    response = await client.post(f"/api/v1/bookings/{booking.json()['id']}/confirm", headers=auth_headers)

    assert response.status_code == 403


async def test_registered_host_can_create_property(client):
    await client.post("/api/v1/auth/register", json={
        "username": "fresh_host",
        "email": "fresh_host@test.com",
        "password": "fresh_password",
        "role": "host",
    })
    tokens = (await client.post(
        "/api/v1/auth/login",
        data={"username": "fresh_host", "password": "fresh_password"},
    )).json()

    response = await client.post(
        "/api/v1/properties/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json=PROPERTY_PAYLOAD,
    )

    assert response.status_code == 201
