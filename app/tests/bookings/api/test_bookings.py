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
            "check_in": "2030-10-01T00:00:00Z",
            "check_out": "2030-10-04T00:00:00Z",
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
            "check_in": "2030-10-01T00:00:00Z",
            "check_out": "2030-10-04T00:00:00Z",
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
            "check_in": "2030-10-05T00:00:00Z",
            "check_out": "2030-10-01T00:00:00Z",
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
            "check_in": "2030-10-01T00:00:00Z",
            "check_out": "2030-10-04T00:00:00Z",
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": property.id,
            "check_in": "2030-10-02T00:00:00Z",
            "check_out": "2030-10-05T00:00:00Z",
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
            "check_in": "2030-11-01T00:00:00Z",
            "check_out": "2030-11-04T00:00:00Z",
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
            "check_in": "2030-12-01T00:00:00Z",
            "check_out": "2030-12-04T00:00:00Z",
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
            "check_in": "2031-01-01T00:00:00Z",
            "check_out": "2031-01-04T00:00:00Z",
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
            "check_in": "2031-02-01T00:00:00Z",
            "check_out": "2031-02-04T00:00:00Z",
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
            "check_in": "2031-04-01T00:00:00Z",
            "check_out": "2031-04-04T00:00:00Z",
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
            "check_in": "2031-05-01T00:00:00Z",
            "check_out": "2031-05-04T00:00:00Z",
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

@pytest.mark.asyncio
async def test_create_booking_for_nonexistent_property(
    client,
    auth_headers,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": 999999,
            "check_in": "2031-08-01T00:00:00Z",
            "check_out": "2031-08-04T00:00:00Z",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_booking_over_capacity(
    client,
    auth_headers,
    owner_property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "check_in": "2031-08-01T00:00:00Z",
            "check_out": "2031-08-04T00:00:00Z",
            "guests": owner_property.guest_capacity + 1,
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_in_past(
    client,
    auth_headers,
    owner_property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "check_in": "2020-01-01T00:00:00Z",
            "check_out": "2020-01-04T00:00:00Z",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_with_zero_guests(
    client,
    auth_headers,
    owner_property,
):
    response = await client.post(
        "/api/v1/bookings/",
        headers=auth_headers,
        json={
            "property_id": owner_property.id,
            "check_in": "2031-08-01T00:00:00Z",
            "check_out": "2031-08-04T00:00:00Z",
            "guests": 0,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_host_bookings_and_rejection(
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
            "check_in": "2031-09-01T00:00:00Z",
            "check_out": "2031-09-04T00:00:00Z",
            "guests": 2,
        },
    )
    assert create_response.status_code == 201
    booking_id = create_response.json()["id"]

    host_response = await client.get(
        "/api/v1/bookings/host",
        headers=owner_auth_headers,
        params={"status": "pending"},
    )
    assert host_response.status_code == 200
    data = host_response.json()
    assert data["total"] == 1
    assert data["bookings"][0]["id"] == booking_id
    assert data["bookings"][0]["guests"] == 2

    owner_view = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=owner_auth_headers,
    )
    assert owner_view.status_code == 200

    reject_response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=owner_auth_headers,
    )
    assert reject_response.status_code == 204

    guest_view = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers=auth_headers,
    )
    assert guest_view.json()["status"] == "cancelled"

    notifications = await client.get(
        "/api/v1/notifications/",
        headers=auth_headers,
    )
    assert notifications.json()["notifications"][0]["type"] == "booking_cancelled"


@pytest.mark.asyncio
async def test_host_bookings_forbidden_for_regular_user(
    client,
    auth_headers,
):
    response = await client.get(
        "/api/v1/bookings/host",
        headers=auth_headers,
    )

    assert response.status_code == 403
