"""Сквозные сценарии нескольких инстансов: приложение и «второй инстанс» делят только Redis.

Второй инстанс — отдельный ConnectionManager с собственным клиентом Redis и подпиской,
как у другого воркера Gunicorn или другого контейнера за nginx.
"""
import pytest

from app.websocket.manager import chat_manager, property_viewers_manager
from app.tests.ws import FakeWebSocket, instance_manager, open_ws

pytestmark = pytest.mark.asyncio


def token_of(headers: dict) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


async def test_chat_message_reaches_participant_on_other_instance(
    client, auth_headers, owner_auth_headers, owner,
):
    response = await client.post("/api/v1/chats/", headers=auth_headers, json={"participant_id": owner.id})
    chat_id = response.json()["id"]

    async with instance_manager(chat_manager.namespace) as other_instance:
        owner_socket = FakeWebSocket()
        await other_instance.connect(chat_id, owner_socket, user_id=owner.id)

        async with open_ws(f"http://test/api/v1/chats/{chat_id}/ws?token={token_of(auth_headers)}") as ws:
            assert (await ws.receive_json())["type"] == "connected"
            await ws.send_json({"content": "Привет с другого воркера"})

            own_event = await ws.receive_json()
            assert own_event["message"]["content"] == "Привет с другого воркера"

        event = await owner_socket.next_event()
        assert event["type"] == "message"
        assert event["message"]["content"] == "Привет с другого воркера"

    # Владелец был онлайн на другом инстансе, поэтому уведомление о сообщении не создается
    notifications = await client.get("/api/v1/notifications/", headers=owner_auth_headers)
    assert notifications.json()["notifications"] == []


async def test_chat_participant_offline_on_all_instances_gets_notification(
    client, auth_headers, owner_auth_headers, owner,
):
    response = await client.post("/api/v1/chats/", headers=auth_headers, json={"participant_id": owner.id})
    chat_id = response.json()["id"]

    async with instance_manager(chat_manager.namespace) as other_instance:
        listener = FakeWebSocket()
        await other_instance.connect(chat_id, listener, user_id=None)

        await client.post(f"/api/v1/chats/{chat_id}/messages", headers=auth_headers, json={"content": "Ау"})
        assert (await listener.next_event())["message"]["content"] == "Ау"

    notifications = await client.get("/api/v1/notifications/", headers=owner_auth_headers)
    assert notifications.json()["notifications"][0]["type"] == "new_message"


async def test_viewers_are_counted_across_instances(client, owner_property):
    property_id = owner_property.id

    async with instance_manager(property_viewers_manager.namespace) as other_instance:
        remote_viewer = FakeWebSocket()
        await other_instance.connect(property_id, remote_viewer, user_id=None)

        async with open_ws(f"http://test/api/v1/properties/{property_id}/viewers/ws") as ws:
            # Зритель на другом инстансе учитывается, и обновление счетчика доходит до обоих
            assert (await ws.receive_json())["count"] == 2
            assert (await remote_viewer.next_event())["count"] == 2

            signals = await client.get(f"/api/v1/properties/{property_id}/signals")
            assert signals.json()["viewing_now"] == 2

        assert (await remote_viewer.next_event())["count"] == 1

    signals = await client.get(f"/api/v1/properties/{property_id}/signals")
    assert signals.json()["viewing_now"] == 0
