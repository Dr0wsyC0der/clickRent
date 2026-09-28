import pytest

pytestmark = pytest.mark.asyncio


async def test_get_me(client, auth_headers):
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "api_test_user"
    assert data["email"] == "api_test@test.com"
    assert data["id"] is not None

    assert "password" not in data
    assert "password_hash" not in data


async def test_get_me_unauthorized(client):
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


async def test_update_me(client, auth_headers):
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "first_name": "Alex",
            "last_name": "Testov",
            "phone_number": "+79991234567",
            "avatar_url": "avatars/test.jpg",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Alex"
    assert data["last_name"] == "Testov"
    assert data["phone_number"] == "+79991234567"
    assert data["avatar_url"] == "avatars/test.jpg"


async def test_update_me_partial(client, auth_headers):
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "first_name": "Updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Updated"


async def test_update_me_unauthorized(client):
    response = await client.patch(
        "/api/v1/users/me",
        json={
            "first_name": "Hacker",
        },
    )

    assert response.status_code == 401


async def test_update_me_does_not_change_role(client, auth_headers):
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "first_name": "Alex",
            "role": "admin",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["role"] != "admin"