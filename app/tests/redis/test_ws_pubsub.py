import asyncio

import pytest

from app.tests.ws import FakeWebSocket, instance_manager

pytestmark = pytest.mark.asyncio

NAMESPACE = "test"


async def test_broadcast_reaches_connections_of_all_instances():
    async with instance_manager(NAMESPACE) as first, instance_manager(NAMESPACE) as second:
        on_first, on_second, other_room = FakeWebSocket(), FakeWebSocket(), FakeWebSocket()
        await first.connect(1, on_first, user_id=10)
        await second.connect(1, on_second, user_id=20)
        await second.connect(2, other_room, user_id=30)

        await first.broadcast(1, {"type": "message", "text": "привет"})

        assert await on_first.next_event() == {"type": "message", "text": "привет"}
        assert await on_second.next_event() == {"type": "message", "text": "привет"}
        await asyncio.sleep(0.2)
        assert other_room.received.empty()


async def test_presence_is_shared_between_instances():
    async with instance_manager(NAMESPACE) as first, instance_manager(NAMESPACE) as second:
        tab_one, tab_two = FakeWebSocket(), FakeWebSocket()
        await first.connect(1, tab_one, user_id=10)
        await second.connect(1, tab_two, user_id=10)
        await first.connect(1, FakeWebSocket())
        await second.connect(1, FakeWebSocket(), user_id=20)

        # Пользователь 10 с двумя вкладками на разных инстансах считается один раз, аноним — отдельно
        assert await first.count_users(1) == 3
        assert await second.count_users(1) == 3
        assert await first.is_user_connected(1, 20)
        assert not await first.is_user_connected(1, 99)

        await second.disconnect(1, tab_two)
        assert await first.is_user_connected(1, 10)

        await first.disconnect(1, tab_one)
        assert not await second.is_user_connected(1, 10)
        assert await second.count_users(1) == 2


async def test_namespaces_are_isolated():
    async with instance_manager("chat-test") as chats, instance_manager("viewers-test") as viewers:
        chat_socket, viewer_socket = FakeWebSocket(), FakeWebSocket()
        await chats.connect(1, chat_socket, user_id=10)
        await viewers.connect(1, viewer_socket, user_id=10)

        await chats.broadcast(1, {"type": "message"})

        assert await chat_socket.next_event() == {"type": "message"}
        await asyncio.sleep(0.2)
        assert viewer_socket.received.empty()
        assert await viewers.count_users(1) == 1


async def test_presence_of_crashed_instance_expires():
    async with instance_manager(NAMESPACE, presence_ttl_seconds=1, heartbeat_interval_seconds=60) as crashed:
        await crashed.connect(1, FakeWebSocket(), user_id=10)
        assert await crashed.count_users(1) == 1

        # Heartbeat не продлевает запись (инстанс «завис»), и через TTL она перестает учитываться
        await asyncio.sleep(1.2)
        assert await crashed.count_users(1) == 0


async def test_heartbeat_keeps_presence_alive():
    async with instance_manager(NAMESPACE, presence_ttl_seconds=1, heartbeat_interval_seconds=0.2) as alive:
        await alive.connect(1, FakeWebSocket(), user_id=10)

        await asyncio.sleep(1.5)

        assert await alive.count_users(1) == 1


async def test_stop_removes_presence_of_instance():
    async with instance_manager(NAMESPACE) as observer:
        async with instance_manager(NAMESPACE) as stopping:
            await stopping.connect(1, FakeWebSocket(), user_id=10)
            assert await observer.count_users(1) == 1

        assert await observer.count_users(1) == 0


async def test_broken_connection_is_removed_on_delivery():
    async with instance_manager(NAMESPACE) as manager:
        broken, healthy = FakeWebSocket(fail=True), FakeWebSocket()
        await manager.connect(1, broken, user_id=10)
        await manager.connect(1, healthy, user_id=20)

        await manager.broadcast(1, {"type": "ping"})

        assert await healthy.next_event() == {"type": "ping"}
        assert manager.local_connections_count(1) == 1
        assert not await manager.is_user_connected(1, 10)


async def test_redis_failures_do_not_break_websocket_flow():
    class BrokenRedis:
        async def publish(self, *args, **kwargs):
            raise ConnectionError("redis is down")

        def pipeline(self, *args, **kwargs):
            raise ConnectionError("redis is down")

    async with instance_manager(NAMESPACE) as manager:
        redis = manager._redis
        manager._redis = BrokenRedis()
        try:
            # Публикация события не роняет обработчик, а без данных о присутствии
            # пользователь считается не подключенным (получит уведомление)
            await manager.broadcast(1, {"type": "ping"})
            assert not await manager.is_user_connected(1, 10)
        finally:
            manager._redis = redis
