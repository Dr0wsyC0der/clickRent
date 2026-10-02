import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.core.config import settings
from app.core.redis import redis_key

logger = logging.getLogger(__name__)

ANONYMOUS = "-"


class ConnectionManager:
    """WebSocket-подключения, сгруппированные по комнатам (чат, объект недвижимости).

    Сами сокеты живут в памяти процесса, а общее состояние — в Redis, поэтому приложение
    может работать в нескольких воркерах и инстансах:

    - broadcast публикует событие в канал Redis комнаты; каждый процесс подписан на каналы
      своего пространства имен и доставляет событие своим локальным подключениям;
    - присутствие (кто подключен к комнате) хранится в sorted set: участник — подключение,
      score — время последнего heartbeat. Записи процесса, который упал без disconnect,
      перестают учитываться через `presence_ttl_seconds`.
    """

    def __init__(
        self,
        namespace: str,
        presence_ttl_seconds: int = settings.ws_presence_ttl_seconds,
        heartbeat_interval_seconds: int = settings.ws_heartbeat_interval_seconds,
    ) -> None:
        self.namespace = namespace
        self.presence_ttl_seconds = presence_ttl_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        # Комната -> {сокет: участник sorted set присутствия}
        self._rooms: dict[str, dict[WebSocket, str]] = defaultdict(dict)
        self._redis: Redis | None = None
        self._pubsub: PubSub | None = None
        self._tasks: list[asyncio.Task] = []

    async def start(self, redis: Redis) -> None:
        self._redis = redis
        self._pubsub = redis.pubsub(ignore_subscribe_messages=True)
        # Подписка выполняется до запуска слушателя, чтобы не потерять первые события
        await self._pubsub.psubscribe(self._channel("*"))
        self._tasks = [
            asyncio.create_task(self._listen(), name=f"ws-{self.namespace}-listener"),
            asyncio.create_task(self._heartbeat(), name=f"ws-{self.namespace}-heartbeat"),
        ]

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with suppress(asyncio.CancelledError):
                await task
        self._tasks = []

        # Убираем присутствие подключений этого процесса, чтобы счетчики не ждали TTL
        for room in list(self._rooms):
            for websocket in list(self._rooms[room]):
                await self.disconnect(room, websocket)

        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None
        self._redis = None

    async def connect(self, room: Any, websocket: WebSocket, user_id: int | None = None) -> None:
        room = str(room)
        member = f"{uuid.uuid4().hex}:{user_id if user_id is not None else ANONYMOUS}"
        self._rooms[room][websocket] = member

        key = self._presence_key(room)
        async with self._get_redis().pipeline(transaction=True) as pipe:
            pipe.zadd(key, {member: time.time()})
            pipe.expire(key, self.presence_ttl_seconds)
            await pipe.execute()

    async def disconnect(self, room: Any, websocket: WebSocket) -> None:
        room = str(room)
        connections = self._rooms.get(room)
        if connections is None:
            return
        member = connections.pop(websocket, None)
        if not connections:
            del self._rooms[room]
        if member is None:
            return

        try:
            await self._get_redis().zrem(self._presence_key(room), member)
        except Exception:
            # Запись исчезнет сама по истечении TTL присутствия
            logger.warning("Не удалось удалить присутствие WebSocket-подключения из Redis", exc_info=True)

    async def is_user_connected(self, room: Any, user_id: int) -> bool:
        try:
            user_ids = await self._active_user_ids(str(room))
        except Exception:
            # Без данных о присутствии считаем пользователя не подключенным: лучше лишнее уведомление
            logger.warning("Не удалось получить присутствие WebSocket-подключений из Redis", exc_info=True)
            return False
        return str(user_id) in user_ids

    async def count_users(self, room: Any) -> int:
        """Количество уникальных зрителей во всех процессах: пользователь с несколькими вкладками
        считается один раз, каждое анонимное подключение — отдельно."""
        user_ids = await self._active_user_ids(str(room))
        authenticated = {user_id for user_id in user_ids if user_id != ANONYMOUS}
        anonymous = sum(1 for user_id in user_ids if user_id == ANONYMOUS)
        return len(authenticated) + anonymous

    async def broadcast(self, room: Any, payload: dict[str, Any]) -> None:
        """Отправляет событие всем подключениям комнаты во всех процессах."""
        try:
            await self._get_redis().publish(self._channel(room), json.dumps(payload, ensure_ascii=False))
        except Exception:
            # Событие не критично: данные уже сохранены, клиент получит их из истории
            logger.exception("Не удалось опубликовать WebSocket-событие в Redis")

    def local_connections_count(self, room: Any) -> int:
        return len(self._rooms.get(str(room), {}))

    async def _active_user_ids(self, room: str) -> list[str]:
        key = self._presence_key(room)
        async with self._get_redis().pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, "-inf", time.time() - self.presence_ttl_seconds)
            pipe.zrange(key, 0, -1)
            _, members = await pipe.execute()
        return [member.rsplit(":", 1)[1] for member in members]

    async def _listen(self) -> None:
        prefix_length = len(self._channel(""))
        while True:
            try:
                async for message in self._pubsub.listen():
                    if message["type"] != "pmessage":
                        continue
                    await self._deliver_local(message["channel"][prefix_length:], message["data"])
            except asyncio.CancelledError:
                raise
            except Exception:
                # redis-py переподключается и восстанавливает подписки при следующем чтении
                logger.exception("Ошибка подписки Redis Pub/Sub (%s), переподключение", self.namespace)
                await asyncio.sleep(1)

    async def _deliver_local(self, room: str, data: str) -> None:
        for websocket in list(self._rooms.get(room, {})):
            try:
                await websocket.send_text(data)
            except Exception:
                logger.warning("Не удалось отправить сообщение по WebSocket, подключение удалено")
                await self.disconnect(room, websocket)

    async def _heartbeat(self) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_interval_seconds)
            try:
                await self.refresh_presence()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Не удалось обновить присутствие WebSocket-подключений в Redis")

    async def refresh_presence(self) -> None:
        """Продлевает присутствие всех локальных подключений процесса."""
        if not self._rooms:
            return
        now = time.time()
        async with self._get_redis().pipeline(transaction=False) as pipe:
            for room, connections in self._rooms.items():
                key = self._presence_key(room)
                pipe.zadd(key, {member: now for member in connections.values()})
                pipe.expire(key, self.presence_ttl_seconds)
            await pipe.execute()

    def _get_redis(self) -> Redis:
        if self._redis is None:
            raise RuntimeError(f"Менеджер WebSocket-подключений '{self.namespace}' не запущен")
        return self._redis

    def _channel(self, room: Any) -> str:
        return redis_key("ws", self.namespace, room)

    def _presence_key(self, room: str) -> str:
        return redis_key("ws-presence", self.namespace, room)


chat_manager = ConnectionManager("chat")
property_viewers_manager = ConnectionManager("viewers")
