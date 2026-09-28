import pytest
from decimal import Decimal
from app.models.properties import Property

@pytest.mark.asyncio
async def test_add_favorite(client, auth_headers, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Недвижимость успешно добавлена в избранное."


@pytest.mark.asyncio
async def test_add_favorite_without_auth(client, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_favorite_nonexistent_property(client, auth_headers):
    response = await client.post(
        "/api/v1/favorites/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_favorite_twice(client, auth_headers, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201

    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_favorites_empty(client, auth_headers):
    response = await client.get(
        "/api/v1/favorites/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["properties"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 0


@pytest.mark.asyncio
async def test_get_favorites(client, auth_headers, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201

    response = await client.get(
        "/api/v1/favorites/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["properties"]) == 1
    assert data["properties"][0]["id"] == property.id


@pytest.mark.asyncio
async def test_get_favorites_without_auth(client):
    response = await client.get("/api/v1/favorites/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_favorite(client, auth_headers, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201

    response = await client.delete(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_favorite_without_auth(client, property):
    response = await client.delete(
        f"/api/v1/favorites/{property.id}",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_nonexistent_favorite(client, auth_headers, property):
    response = await client.delete(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_favorite_removed_from_list(client, auth_headers, property):
    response = await client.post(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 201

    response = await client.delete(
        f"/api/v1/favorites/{property.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        "/api/v1/favorites/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["properties"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_favorites_pagination(
    client,
    auth_headers,
    db_session,
    guest,
    property,
):
    property_2 = Property(
        owner_id=guest.id,
        title="Second apartment",
        description="Second test apartment",
        price_per_night=Decimal("120.00"),
        country="Russia",
        city="Moscow",
        address="Test street, 2",
        rooms=2,
        beds=2,
        bathrooms=1,
        guest_capacity=4,
    )

    property_3 = Property(
        owner_id=guest.id,
        title="Third apartment",
        description="Third test apartment",
        price_per_night=Decimal("150.00"),
        country="Russia",
        city="Moscow",
        address="Test street, 3",
        rooms=3,
        beds=3,
        bathrooms=2,
        guest_capacity=6,
    )

    db_session.add_all([property_2, property_3])
    await db_session.flush()

    for property_id in [property.id, property_2.id, property_3.id]:
        response = await client.post(
            f"/api/v1/favorites/{property_id}",
            headers=auth_headers,
        )
        assert response.status_code == 201

    response = await client.get(
        "/api/v1/favorites/?page=1&size=2",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] == 2
    assert len(data["properties"]) == 2