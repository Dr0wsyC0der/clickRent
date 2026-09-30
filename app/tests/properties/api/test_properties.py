import pytest
from app.models.amenities import Amenity
from sqlalchemy import select
from app.models.property_views import PropertyView

PROPERTY_DATA = {
    "title": "Test apartment",
    "description": "Beautiful test apartment",
    "beds": 2,
    "bathrooms": 1,
    "guest_capacity": 4,
    "rooms": 2,
    "country": "Russia",
    "city": "Moscow",
    "address": "Test street, 1",
    "price_per_night": 100.00,
}


@pytest.mark.asyncio
async def test_create_property(client, owner_auth_headers):
    response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Test apartment"
    assert data["description"] == "Beautiful test apartment"
    assert data["beds"] == 2
    assert data["bathrooms"] == 1
    assert data["guest_capacity"] == 4
    assert data["rooms"] == 2
    assert data["country"] == "Russia"
    assert data["city"] == "Moscow"
    assert data["price_per_night"] == 100.0
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_property_without_auth(client):
    response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_all_properties(
    client,
    owner_auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    response = await client.get("/api/v1/properties/")

    assert response.status_code == 200

    data = response.json()

    assert "properties" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    assert data["total"] == 1
    assert len(data["properties"]) == 1
    assert data["properties"][0]["title"] == "Test apartment"


@pytest.mark.asyncio
async def test_get_all_properties_pagination(
    client,
    owner_auth_headers,
):
    for i in range(3):
        property_data = {
            **PROPERTY_DATA,
            "title": f"Apartment {i}",
            "address": f"Test street, {i}",
        }

        response = await client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=owner_auth_headers,
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/properties/",
        params={
            "page": 1,
            "size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["pages"] == 2
    assert len(data["properties"]) == 2


@pytest.mark.asyncio
async def test_get_property_by_id(
    client,
    owner_auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/properties/{property_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == property_id
    assert data["title"] == "Test apartment"
    assert data["city"] == "Moscow"

@pytest.mark.asyncio
async def test_guest_property_view(
    client,
    owner_auth_headers,
    db_session,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/properties/{property_id}"
    )

    assert response.status_code == 200

    # Гостю должен выдаться visitor_id
    assert "visitor_id" in response.cookies

    visitor_id = response.cookies["visitor_id"]
    assert visitor_id


@pytest.mark.asyncio
async def test_guest_property_view_not_duplicated(
    client,
    owner_auth_headers,
    db_session,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    # Первое открытие
    first_response = await client.get(
        f"/api/v1/properties/{property_id}"
    )

    assert first_response.status_code == 200

    # Второе открытие тем же клиентом
    second_response = await client.get(
        f"/api/v1/properties/{property_id}"
    )

    assert second_response.status_code == 200

    result = await db_session.execute(
        select(PropertyView).where(
            PropertyView.property_id == property_id
        )
    )

    views = result.scalars().all()

    assert len(views) == 1
    assert views[0].visitor_id is not None
    assert views[0].user_id is None


@pytest.mark.asyncio
async def test_authenticated_user_property_view(
    client,
    owner_auth_headers,
    auth_headers,
    db_session,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/properties/{property_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(PropertyView).where(
            PropertyView.property_id == property_id
        )
    )

    views = result.scalars().all()

    assert len(views) == 1
    assert views[0].user_id is not None
    assert views[0].visitor_id is None


@pytest.mark.asyncio
async def test_authenticated_user_property_view_not_duplicated(
    client,
    owner_auth_headers,
    auth_headers,
    db_session,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    # Первое открытие
    first_response = await client.get(
        f"/api/v1/properties/{property_id}",
        headers=auth_headers,
    )

    assert first_response.status_code == 200

    # Второе открытие
    second_response = await client.get(
        f"/api/v1/properties/{property_id}",
        headers=auth_headers,
    )

    assert second_response.status_code == 200

    result = await db_session.execute(
        select(PropertyView).where(
            PropertyView.property_id == property_id
        )
    )

    views = result.scalars().all()

    assert len(views) == 1
    assert views[0].user_id is not None
    assert views[0].visitor_id is None

@pytest.mark.asyncio
async def test_get_nonexistent_property(client):
    response = await client.get(
        "/api/v1/properties/999999"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_host_properties(
    client,
    owner_auth_headers,
):
    for i in range(2):
        property_data = {
            **PROPERTY_DATA,
            "title": f"Owner apartment {i}",
            "address": f"Owner street, {i}",
        }

        response = await client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=owner_auth_headers,
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/properties/host",
        headers=owner_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["owner_id"] == data[1]["owner_id"]


@pytest.mark.asyncio
async def test_get_host_properties_without_auth(client):
    response = await client.get(
        "/api/v1/properties/host"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_property(
    client,
    owner_auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/properties/{property_id}",
        json={
            "title": "Updated apartment",
            "price_per_night": 150.00,
        },
        headers=owner_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == property_id
    assert data["title"] == "Updated apartment"
    assert data["price_per_night"] == 150.0


@pytest.mark.asyncio
async def test_update_property_by_not_owner(
    client,
    owner_auth_headers,
    auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/properties/{property_id}",
        json={
            "title": "Hacked apartment",
        },
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_property(
    client,
    owner_auth_headers,
):
    response = await client.patch(
        "/api/v1/properties/999999",
        json={
            "title": "Updated apartment",
        },
        headers=owner_auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_property(
    client,
    owner_auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/properties/{property_id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204

    get_response = await client.get(
        f"/api/v1/properties/{property_id}"
    )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_property_by_not_owner(
    client,
    owner_auth_headers,
    auth_headers,
):
    create_response = await client.post(
        "/api/v1/properties/",
        json=PROPERTY_DATA,
        headers=owner_auth_headers,
    )

    assert create_response.status_code == 201

    property_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/properties/{property_id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_nonexistent_property(
    client,
    owner_auth_headers,
):
    response = await client.delete(
        "/api/v1/properties/999999",
        headers=owner_auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_properties(
    client,
    owner_auth_headers,
):
    properties = [
        {
            **PROPERTY_DATA,
            "title": "Moscow apartment",
            "city": "Moscow",
            "address": "Moscow street, 1",
            "price_per_night": 100.00,
        },
        {
            **PROPERTY_DATA,
            "title": "SPB apartment",
            "city": "Saint Petersburg",
            "address": "Nevsky avenue, 1",
            "price_per_night": 200.00,
        },
    ]

    for property_data in properties:
        response = await client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=owner_auth_headers,
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/properties/search",
        params={
            "city": "Moscow",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["properties"]) == 1
    assert data["properties"][0]["city"] == "Moscow"


@pytest.mark.asyncio
async def test_search_properties_by_price(
    client,
    owner_auth_headers,
):
    properties = [
        {
            **PROPERTY_DATA,
            "title": "Cheap apartment",
            "address": "Cheap street, 1",
            "price_per_night": 100.00,
        },
        {
            **PROPERTY_DATA,
            "title": "Expensive apartment",
            "address": "Expensive street, 1",
            "price_per_night": 500.00,
        },
    ]

    for property_data in properties:
        response = await client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=owner_auth_headers,
        )

        assert response.status_code == 201

    response = await client.get(
        "/api/v1/properties/search",
        params={
            "min_price": 400,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["properties"][0]["price_per_night"] == 500.0

@pytest.mark.asyncio
async def test_add_amenity_to_property(
    client,
    db_session,
    owner_auth_headers,
    owner_property,
):
    amenity = Amenity(
        name="Wi-Fi",
        description="Free Wi-Fi",
    )
    db_session.add(amenity)
    await db_session.flush()

    response = await client.post(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/properties/{owner_property.id}/amenities"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == amenity.id
    assert data[0]["name"] == "Wi-Fi"

@pytest.mark.asyncio
async def test_add_nonexistent_amenity(
    client,
    owner_auth_headers,
    owner_property,
):
    response = await client.post(
        f"/api/v1/properties/{owner_property.id}/amenities/999999",
        headers=owner_auth_headers,
    )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_add_amenity_by_non_host(
    client,
    db_session,
    auth_headers,
    owner_property,
):
    amenity = Amenity(
        name="Parking",
        description="Free parking",
    )
    db_session.add(amenity)
    await db_session.flush()

    response = await client.post(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_remove_amenity_from_property(
    client,
    db_session,
    owner_auth_headers,
    owner_property,
):
    amenity = Amenity(
        name="Air conditioning",
        description="Air conditioning in every room",
    )
    db_session.add(amenity)
    await db_session.flush()

    response = await client.post(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204

    response = await client.delete(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/properties/{owner_property.id}/amenities"
    )

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_remove_not_added_amenity(
    client,
    db_session,
    owner_auth_headers,
    owner_property,
):
    amenity = Amenity(
        name="Pool",
        description="Swimming pool",
    )
    db_session.add(amenity)
    await db_session.flush()

    response = await client.delete(
        f"/api/v1/properties/{owner_property.id}/amenities/{amenity.id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 409