import pytest


@pytest.mark.asyncio
async def test_create_booking(
    client,
    auth_headers,
    property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-10-01T00:00:00Z",
            "check_out": "2026-10-04T00:00:00Z",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["property_id"] == property.id
    assert data["status"] == "pending"
    assert data["total_price"] == 300.0


@pytest.mark.asyncio
async def test_create_booking_without_auth(
    client,
    property,
):
    response = await client.post(
        "/api/v1/bookings/",
        json={
            "property_id": property.id,
            "check_in": "2026-10-01T00:00:00Z",
            "check_out": "2026-10-04T00:00:00Z",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_booking_with_invalid_dates(
    client,
    auth_headers,
    property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-10-05T00:00:00Z",
            "check_out": "2026-10-01T00:00:00Z",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_with_intersection(
    client,
    auth_headers,
    property,
):
    first_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-10-01T00:00:00Z",
            "check_out": "2026-10-04T00:00:00Z",
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-10-02T00:00:00Z",
            "check_out": "2026-10-05T00:00:00Z",
        },
    )

    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_get_my_bookings(
    client,
    auth_headers,
    property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-11-01T00:00:00Z",
            "check_out": "2026-11-04T00:00:00Z",
        },
    )

    assert response.status_code == 201

    response = await client.get(
        "/api/v1/bookings/my",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 1
    assert len(data["bookings"]) == 1


@pytest.mark.asyncio
async def test_get_my_bookings_without_auth(
    client,
):
    response = await client.get(
        "/api/v1/bookings/my",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_booking_by_id(
    client,
    auth_headers,
    property,
):
    create_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2026-12-01T00:00:00Z",
            "check_out": "2026-12-04T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["property_id"] == property.id
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_nonexistent_booking(
    client,
    auth_headers,
):
    response = await client.get(
        "/api/v1/bookings/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_booking(
    client,
    auth_headers,
    property,
):
    create_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2027-01-01T00:00:00Z",
            "check_out": "2027-01-04T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(
    client,
    auth_headers,
    property,
):
    create_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2027-02-01T00:00:00Z",
            "check_out": "2027-02-04T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 204

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirm_booking_by_owner(
    client,
    auth_headers,
    owner_auth_headers,
    owner_property,
):
    create_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "check_in": "2027-04-01T00:00:00Z",
            "check_out": "2027-04-04T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

@pytest.mark.asyncio
async def test_confirm_booking_by_not_owner(
    client,
    auth_headers,
    owner_property,
):
    create_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "check_in": "2027-05-01T00:00:00Z",
            "check_out": "2027-05-04T00:00:00Z",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers,
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_confirm_booking_without_auth(
    client,
):
    response = await client.post(
        "/api/v1/bookings/1/confirm",
    )

    assert response.status_code == 401