from datetime import datetime, timedelta, timezone
import jwt
import pytest
from sqlalchemy import update

from app.core.config import settings
from app.models.refresh_tokens import RefreshToken
from app.models.users import User
from app.security.jwt import create_access_token

pytestmark = pytest.mark.asyncio


async def login(client, username="api_test_user", password="test_password"):
    response = await client.post("/api/v1/auth/login", data={"username": username, "password": password})
    return response


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# -------------------------
# Регистрация
# -------------------------

async def test_register_as_host(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "new_host",
        "email": "new_host@test.com",
        "password": "host_password",
        "role": "host",
    })

    assert response.status_code == 200
    assert response.json()["role"] == "host"


async def test_register_default_role_is_user(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "plain_user",
        "email": "plain_user@test.com",
        "password": "user_password",
    })

    assert response.json()["role"] == "user"


@pytest.mark.parametrize("payload", [
    {"username": "admin_wannabe", "email": "admin@test.com", "password": "admin_password", "role": "admin"},
    {"username": "short_pass", "email": "short@test.com", "password": "123"},
    {"username": "bad_email", "email": "not-an-email", "password": "valid_password"},
    {"email": "no_username@test.com", "password": "valid_password"},
])
async def test_register_invalid_payload(client, payload):
    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


async def test_register_duplicate_has_message(client, api_user):
    response = await client.post("/api/v1/auth/register", json={
        "username": "api_test_user",
        "email": "other@test.com",
        "password": "test_password",
    })

    assert response.status_code == 409
    assert response.json()["detail"]


# -------------------------
# Логин
# -------------------------

async def test_login_with_phone(client, db_session, api_user):
    api_user.phone_number = "+79991234567"
    await db_session.flush()

    response = await login(client, username="+79991234567")

    assert response.status_code == 200


async def test_login_inactive_user(client, db_session, api_user):
    api_user.is_active = False
    await db_session.flush()

    response = await login(client)

    assert response.status_code == 403


async def test_inactive_user_token_rejected(client, db_session, api_user, auth_headers):
    api_user.is_active = False
    await db_session.flush()

    response = await client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 403


# -------------------------
# Access-токен
# -------------------------

async def test_expired_access_token(client, api_user):
    token = jwt.encode(
        {"sub": str(api_user.id), "type": "access", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await client.get("/api/v1/users/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["detail"]


async def test_token_with_wrong_signature(client, api_user):
    token = jwt.encode(
        {"sub": str(api_user.id), "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "another-secret-key-that-is-long-enough-for-hs256",
        algorithm=settings.algorithm,
    )

    response = await client.get("/api/v1/users/me", headers=bearer(token))

    assert response.status_code == 401


async def test_refresh_token_cannot_be_used_as_access(client, api_user):
    tokens = (await login(client)).json()

    response = await client.get("/api/v1/users/me", headers=bearer(tokens["refresh_token"]))

    assert response.status_code == 401


async def test_access_token_for_deleted_user(client):
    token, _ = create_access_token({"sub": "999999"})

    response = await client.get("/api/v1/users/me", headers=bearer(token))

    assert response.status_code == 401


async def test_malformed_authorization_header(client):
    response = await client.get("/api/v1/users/me", headers={"Authorization": "Token abc"})

    assert response.status_code == 401


# -------------------------
# Refresh-токен
# -------------------------

async def test_access_token_cannot_be_used_as_refresh(client, api_user):
    tokens = (await login(client)).json()

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401


async def test_expired_refresh_token(client, db_session, api_user):
    tokens = (await login(client)).json()
    await db_session.execute(
        update(RefreshToken).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    )
    await db_session.flush()

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401
    assert response.json()["detail"] == "Срок действия refresh-токена истек."


async def test_refresh_rotation_chain(client, api_user):
    first = (await login(client)).json()

    second = (await client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})).json()
    third = await client.post("/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]})

    assert third.status_code == 200
    # Повторное использование уже ротированного токена запрещено
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuse.status_code == 401
    assert reuse.json()["detail"] == "Refresh-токен отозван."


async def test_refresh_for_inactive_user(client, db_session, api_user):
    tokens = (await login(client)).json()
    api_user.is_active = False
    await db_session.flush()

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 403


async def test_logout_with_invalid_token(client):
    response = await client.post("/api/v1/auth/logout", json={"refresh_token": "garbage"})

    assert response.status_code == 401


async def test_sessions_are_independent(client, api_user):
    first = (await login(client)).json()
    second = (await login(client)).json()

    await client.post("/api/v1/auth/logout", json={"refresh_token": first["refresh_token"]})
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]})

    assert response.status_code == 200
