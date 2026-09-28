import pytest


pytestmark = pytest.mark.asyncio


def register_data(
    username="new_user",
    email="new_user@test.com",
    password="test_password",
):
    return {
        "username": username,
        "email": email,
        "password": password,
    }


async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_data(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "new_user"
    assert data["email"] == "new_user@test.com"
    assert "password" not in data
    assert "password_hash" not in data
    assert data["id"] is not None


async def test_register_duplicate_email(client, api_user):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_data(
            username="another_user",
            email="api_test@test.com",
        ),
    )

    assert response.status_code == 409


async def test_register_duplicate_username(client, api_user):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_data(
            username="api_test_user",
            email="another@test.com",
        ),
    )

    assert response.status_code == 409


async def test_login_with_username(client, api_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_with_email(client, api_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test@test.com",
            "password": "test_password",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, api_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401


async def test_login_user_not_found(client):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown_user",
            "password": "test_password",
        },
    )

    assert response.status_code == 401


async def test_refresh_token(client, api_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


async def test_old_refresh_token_is_revoked(client, api_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401


async def test_logout(client, api_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 204


async def test_refresh_after_logout(client, api_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "api_test_user",
            "password": "test_password",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code == 204

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401


async def test_refresh_invalid_token(client):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid_refresh_token",
        },
    )

    assert response.status_code == 401