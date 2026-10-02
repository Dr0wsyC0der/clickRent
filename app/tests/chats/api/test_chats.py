import pytest
import pytest_asyncio
from httpx_ws import WebSocketDisconnect

from app.models.users import User
from app.security.hashing import hash_password
from app.websocket.manager import chat_manager
from app.tests.ws import open_ws

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def outsider_headers(client, db_session):
    user = User(
        username="chat_outsider",
        email="chat_outsider@test.com",
        password_hash=hash_password("outsider_password"),
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "chat_outsider", "password": "outsider_password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def chat(client, auth_headers, owner):
    response = await client.post(
        "/api/v1/chats/",
        headers=auth_headers,
        json={"participant_id": owner.id},
    )
    assert response.status_code == 201
    return response.json()


async def connected(ws):
    event = await ws.receive_json()
    assert event["type"] == "connected"
    return ws


def token_of(headers: dict) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def ws_url(chat_id: int, headers: dict | None = None) -> str:
    url = f"http://test/api/v1/chats/{chat_id}/ws"
    if headers is not None:
        url += f"?token={token_of(headers)}"
    return url


async def get_notifications(client, headers):
    response = await client.get("/api/v1/notifications/", headers=headers)
    return response.json()["notifications"]


# -------------------------
# REST
# -------------------------

async def test_create_chat_is_idempotent(client, auth_headers, owner_auth_headers, api_user, owner, chat):
    assert sorted(chat["participant_ids"]) == sorted([api_user.id, owner.id])
    assert chat["last_message"] is None

    again = await client.post("/api/v1/chats/", headers=auth_headers, json={"participant_id": owner.id})
    reverse = await client.post("/api/v1/chats/", headers=owner_auth_headers, json={"participant_id": api_user.id})

    assert again.status_code == 200
    assert reverse.status_code == 200
    assert again.json()["id"] == chat["id"]
    assert reverse.json()["id"] == chat["id"]


async def test_create_chat_with_self(client, auth_headers, api_user):
    response = await client.post("/api/v1/chats/", headers=auth_headers, json={"participant_id": api_user.id})

    assert response.status_code == 400


async def test_create_chat_with_unknown_user(client, auth_headers):
    response = await client.post("/api/v1/chats/", headers=auth_headers, json={"participant_id": 999999})

    assert response.status_code == 404


async def test_chats_require_auth(client):
    assert (await client.get("/api/v1/chats/")).status_code == 401
    assert (await client.post("/api/v1/chats/", json={"participant_id": 1})).status_code == 401


async def test_send_message_and_history(client, auth_headers, owner_auth_headers, chat):
    for text in ["Здравствуйте!", "Свободно ли на выходных?"]:
        response = await client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            headers=auth_headers,
            json={"content": f"  {text}  "},
        )
        assert response.status_code == 201
        assert response.json()["content"] == text

    history = await client.get(f"/api/v1/chats/{chat['id']}/messages", headers=owner_auth_headers)

    assert history.status_code == 200
    data = history.json()
    assert data["total"] == 2
    assert [m["content"] for m in data["messages"]] == ["Свободно ли на выходных?", "Здравствуйте!"]

    chats = await client.get("/api/v1/chats/", headers=owner_auth_headers)
    assert chats.json()["total"] == 1
    assert chats.json()["chats"][0]["last_message"]["content"] == "Свободно ли на выходных?"


@pytest.mark.parametrize("content", ["", "   ", "x" * 2001])
async def test_send_invalid_message(client, auth_headers, chat, content):
    response = await client.post(
        f"/api/v1/chats/{chat['id']}/messages",
        headers=auth_headers,
        json={"content": content},
    )

    assert response.status_code == 422


async def test_outsider_has_no_access(client, outsider_headers, chat):
    chat_id = chat["id"]

    assert (await client.get(f"/api/v1/chats/{chat_id}", headers=outsider_headers)).status_code == 403
    assert (await client.get(f"/api/v1/chats/{chat_id}/messages", headers=outsider_headers)).status_code == 403
    send = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=outsider_headers,
        json={"content": "Привет"},
    )
    assert send.status_code == 403
    assert (await client.get("/api/v1/chats/", headers=outsider_headers)).json()["total"] == 0


async def test_unknown_chat(client, auth_headers):
    response = await client.get("/api/v1/chats/999999/messages", headers=auth_headers)

    assert response.status_code == 404


async def test_offline_recipient_gets_notification(client, auth_headers, owner_auth_headers, chat):
    await client.post(
        f"/api/v1/chats/{chat['id']}/messages",
        headers=auth_headers,
        json={"content": "Есть вопрос по квартире"},
    )

    owner_notifications = await get_notifications(client, owner_auth_headers)
    sender_notifications = await get_notifications(client, auth_headers)

    assert owner_notifications[0]["type"] == "new_message"
    assert owner_notifications[0]["message"] == "api_test_user: Есть вопрос по квартире"
    assert sender_notifications == []


# -------------------------
# WebSocket
# -------------------------

async def test_ws_realtime_delivery(client, auth_headers, owner_auth_headers, api_user, chat):
    chat_id = chat["id"]

    # Подключаемся по очереди: в тестах все подключения делят одну сессию БД
    async with open_ws(ws_url(chat_id, auth_headers)) as guest_ws:
        await connected(guest_ws)
        async with open_ws(ws_url(chat_id, owner_auth_headers)) as owner_ws:
            await connected(owner_ws)
            await guest_ws.send_json({"content": "Добрый день!"})

            for ws in (guest_ws, owner_ws):
                event = await ws.receive_json()
                assert event["type"] == "message"
                assert event["message"]["content"] == "Добрый день!"
                assert event["message"]["sender_id"] == api_user.id

            # Сообщение, отправленное через REST, тоже приходит по WebSocket
            await client.post(
                f"/api/v1/chats/{chat_id}/messages",
                headers=owner_auth_headers,
                json={"content": "Здравствуйте!"},
            )
            event = await guest_ws.receive_json()
            assert event["message"]["content"] == "Здравствуйте!"

    # Получатели были онлайн — уведомления не нужны
    assert await get_notifications(client, owner_auth_headers) == []
    assert await get_notifications(client, auth_headers) == []

    history = await client.get(f"/api/v1/chats/{chat_id}/messages", headers=auth_headers)
    assert history.json()["total"] == 2


async def test_ws_invalid_payload_keeps_connection(auth_headers, chat):
    async with open_ws(ws_url(chat["id"], auth_headers)) as ws:
        await connected(ws)
        await ws.send_text("not json")
        assert (await ws.receive_json())["type"] == "error"

        await ws.send_json({"content": ""})
        assert (await ws.receive_json())["type"] == "error"

        await ws.send_json({"content": "Теперь корректно"})
        event = await ws.receive_json()
        assert event["type"] == "message"


async def test_ws_disconnect_removes_connection(client, auth_headers, owner_auth_headers, owner, chat):
    chat_id = chat["id"]

    async with open_ws(ws_url(chat_id, owner_auth_headers)) as ws:
        await connected(ws)
        assert chat_manager.is_user_connected(chat_id, owner.id)

    await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=auth_headers,
        json={"content": "Вы здесь?"},
    )

    assert not chat_manager.is_user_connected(chat_id, owner.id)
    notifications = await get_notifications(client, owner_auth_headers)
    assert notifications[0]["type"] == "new_message"


@pytest.mark.parametrize("case, expected_code", [
    ("no_token", 4401),
    ("bad_token", 4401),
    ("outsider", 4403),
    ("unknown_chat", 4404),
])
async def test_ws_rejects_connection(auth_headers, outsider_headers, chat, case, expected_code):
    url = {
        "no_token": ws_url(chat["id"]),
        "bad_token": ws_url(chat["id"]) + "?token=invalid",
        "outsider": ws_url(chat["id"], outsider_headers),
        "unknown_chat": ws_url(999999, auth_headers),
    }[case]

    async with open_ws(url) as ws:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            await ws.receive_text()

    assert exc_info.value.code == expected_code
