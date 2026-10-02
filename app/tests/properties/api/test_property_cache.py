from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import update

from app.api.dependencies.redis import get_redis_client
from app.cache.property import PropertyCache
from app.core.config import settings
from app.db.enums import UserRole
from app.main import app
from app.models.amenities import Amenity
from app.models.properties import Property
from app.models.users import User
from app.security.hashing import hash_password

pytestmark = pytest.mark.asyncio

NEW_PROPERTY = {
    "title": "Новый лофт",
    "beds": 1,
    "bathrooms": 1,
    "guest_capacity": 2,
    "rooms": 1,
    "country": "Russia",
    "city": "Kazan",
    "address": "Bauman street, 10",
    "price_per_night": "90.00",
}


async def change_in_db_directly(db_session, property_id: int, **values) -> None:
    """Изменение в обход сервисов: кэш о нем не знает, так проверяется, что ответ пришел из кэша."""
    await db_session.execute(update(Property).where(Property.id == property_id).values(**values))
    await db_session.flush()


async def cache_keys(redis_client, pattern: str = "clickrent:cache:*") -> list[str]:
    return [key async for key in redis_client.scan_iter(pattern)]


@pytest_asyncio.fixture
async def amenity(db_session):
    amenity = Amenity(name="Сауна")
    db_session.add(amenity)
    await db_session.flush()
    return amenity


@pytest_asyncio.fixture
async def admin_headers(client, db_session):
    db_session.add(User(
        username="cache_admin",
        email="cache_admin@test.com",
        password_hash=hash_password("admin_password"),
        role=UserRole.ADMIN,
    ))
    await db_session.flush()
    response = await client.post("/api/v1/auth/login", data={"username": "cache_admin", "password": "admin_password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_property_detail_is_served_from_cache(client, db_session, owner_property):
    first = await client.get(f"/api/v1/properties/{owner_property.id}")
    await change_in_db_directly(db_session, owner_property.id, title="Изменено в обход API")
    second = await client.get(f"/api/v1/properties/{owner_property.id}")

    assert first.status_code == second.status_code == 200
    assert second.json() == first.json()


async def test_update_invalidates_property_and_catalog(client, owner_auth_headers, owner_property):
    await client.get(f"/api/v1/properties/{owner_property.id}")
    await client.get("/api/v1/properties/")
    await client.get("/api/v1/properties/search", params={"city": "Moscow"})

    response = await client.patch(
        f"/api/v1/properties/{owner_property.id}",
        headers=owner_auth_headers,
        json={"title": "Обновленный лофт", "price_per_night": 250},
    )
    assert response.status_code == 200

    detail = (await client.get(f"/api/v1/properties/{owner_property.id}")).json()
    listing = (await client.get("/api/v1/properties/")).json()
    search = (await client.get("/api/v1/properties/search", params={"city": "Moscow"})).json()

    assert detail["title"] == "Обновленный лофт"
    assert detail["price_per_night"] == 250
    assert listing["properties"][0]["title"] == "Обновленный лофт"
    assert search["properties"][0]["price_per_night"] == 250


async def test_create_invalidates_catalog(client, owner_auth_headers, owner_property):
    before = (await client.get("/api/v1/properties/")).json()
    assert before["total"] == 1

    created = await client.post("/api/v1/properties/", headers=owner_auth_headers, json=NEW_PROPERTY)
    assert created.status_code == 201

    after = (await client.get("/api/v1/properties/")).json()
    search = (await client.get("/api/v1/properties/search", params={"city": "Kazan"})).json()

    assert after["total"] == 2
    assert search["properties"][0]["id"] == created.json()["id"]


async def test_delete_invalidates_property_and_catalog(client, owner_auth_headers, owner_property):
    assert (await client.get(f"/api/v1/properties/{owner_property.id}")).status_code == 200
    assert (await client.get("/api/v1/properties/")).json()["total"] == 1

    response = await client.delete(f"/api/v1/properties/{owner_property.id}", headers=owner_auth_headers)
    assert response.status_code == 204

    assert (await client.get(f"/api/v1/properties/{owner_property.id}")).status_code == 404
    assert (await client.get("/api/v1/properties/")).json()["total"] == 0


async def test_amenity_changes_invalidate_search(client, owner_auth_headers, owner_property, amenity):
    params = {"amenity_ids": [amenity.id]}
    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 0

    added = await client.post(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}", headers=owner_auth_headers,
    )
    assert added.status_code == 204
    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 1

    removed = await client.delete(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}", headers=owner_auth_headers,
    )
    assert removed.status_code == 204
    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 0


async def test_amenity_deletion_invalidates_search(
    client, owner_auth_headers, admin_headers, owner_property, amenity,
):
    await client.post(f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}", headers=owner_auth_headers)
    params = {"amenity_ids": [amenity.id]}
    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 1

    deleted = await client.delete(f"/api/v1/amenities/{amenity.id}", headers=admin_headers)
    assert deleted.status_code == 204

    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 0


async def test_rating_change_invalidates_property_and_catalog(
    client, auth_headers, owner_property, completed_booking,
):
    await client.get(f"/api/v1/properties/{owner_property.id}")
    await client.get("/api/v1/properties/search", params={"sort_by": "rating"})

    review = await client.post("/api/v1/reviews/", headers=auth_headers, json={
        "property_id": owner_property.id, "booking_id": completed_booking.id, "rating": 4,
    })
    assert review.status_code == 201

    detail = (await client.get(f"/api/v1/properties/{owner_property.id}")).json()
    search = (await client.get("/api/v1/properties/search", params={"sort_by": "rating"})).json()
    assert detail["rating"] == 4
    assert detail["review_count"] == 1
    assert search["properties"][0]["rating"] == 4

    await client.patch(f"/api/v1/reviews/{review.json()['id']}", headers=auth_headers, json={"rating": 2})
    assert (await client.get(f"/api/v1/properties/{owner_property.id}")).json()["rating"] == 2

    await client.delete(f"/api/v1/reviews/{review.json()['id']}", headers=auth_headers)
    detail = (await client.get(f"/api/v1/properties/{owner_property.id}")).json()
    assert detail["rating"] is None
    assert detail["review_count"] == 0


@pytest.mark.parametrize("params", [
    {"check_in": "2031-03-01T12:00:00Z", "check_out": "2031-03-05T12:00:00Z"},
    {"sort_by": "popularity"},
])
async def test_volatile_searches_are_not_cached(client, redis_client, owner_property, params):
    response = await client.get("/api/v1/properties/search", params=params)

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert await cache_keys(redis_client, "clickrent:cache:catalog:*") == []


async def test_search_by_dates_reflects_new_booking(client, auth_headers, owner_property):
    params = {"check_in": "2031-03-01T12:00:00Z", "check_out": "2031-03-05T12:00:00Z"}
    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 1

    booking = await client.post("/api/v1/bookings/", headers=auth_headers, json={
        "property_id": owner_property.id, **params,
    })
    assert booking.status_code == 201

    assert (await client.get("/api/v1/properties/search", params=params)).json()["total"] == 0


async def test_cache_can_be_disabled(client, db_session, redis_client, owner_property, monkeypatch):
    monkeypatch.setattr(settings, "cache_enabled", False)

    await client.get(f"/api/v1/properties/{owner_property.id}")
    await change_in_db_directly(db_session, owner_property.id, title="Без кэша")
    response = await client.get(f"/api/v1/properties/{owner_property.id}")

    assert response.json()["title"] == "Без кэша"
    assert await cache_keys(redis_client) == []


async def test_cache_entries_have_ttl(client, redis_client, owner_property):
    await client.get(f"/api/v1/properties/{owner_property.id}")
    await client.get("/api/v1/properties/")

    data_keys = [key for key in await cache_keys(redis_client) if not key.endswith(":version")]

    assert len(data_keys) == 2
    for key in data_keys:
        assert await redis_client.ttl(key) > 0


async def test_properties_work_without_redis(client, owner_auth_headers, owner_property):
    class BrokenRedis:
        async def get(self, *args, **kwargs):
            raise ConnectionError("redis is down")

        def pipeline(self, *args, **kwargs):
            raise ConnectionError("redis is down")

    app.dependency_overrides[get_redis_client] = lambda: BrokenRedis()

    assert (await client.get(f"/api/v1/properties/{owner_property.id}")).status_code == 200
    assert (await client.get("/api/v1/properties/")).json()["total"] == 1
    updated = await client.patch(
        f"/api/v1/properties/{owner_property.id}", headers=owner_auth_headers, json={"title": "Без Redis"},
    )
    assert updated.status_code == 200
    assert (await client.get(f"/api/v1/properties/{owner_property.id}")).json()["title"] == "Без Redis"


async def test_concurrent_read_does_not_cache_stale_data(redis_client, db_session, owner_property):
    """Чтение началось до изменения, а записало результат после инвалидации: свежие данные не перекрываются."""
    cache = PropertyCache(redis_client, enabled=True, property_ttl_seconds=300, catalog_ttl_seconds=60)
    stale_snapshot = Property(**{
        column.name: getattr(owner_property, column.name) for column in Property.__table__.columns
    })
    stale_snapshot.rating = Decimal("1.0")

    async def slow_loader_with_concurrent_update():
        # Пока запрос читает БД, другой запрос изменил объект и инвалидировал кэш
        await cache.invalidate_property(owner_property.id)
        return stale_snapshot

    stale = await cache.get_property(owner_property.id, slow_loader_with_concurrent_update)
    assert stale.rating == Decimal("1.0")

    async def fresh_loader():
        return owner_property

    fresh = await cache.get_property(owner_property.id, fresh_loader)
    assert fresh is owner_property
