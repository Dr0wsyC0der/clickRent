import logging
from collections import defaultdict
from collections.abc import Hashable
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Хранит активные WebSocket-подключения, сгруппированные по комнатам (чат, объект недвижимости).

    Состояние живет в памяти процесса, поэтому приложение с WebSocket запускается одним воркером.
    Для горизонтального масштабирования менеджер нужно заменить на брокер (например, Redis Pub/Sub).
    """

    def __init__(self) -> None:
        self._rooms: dict[Hashable, dict[WebSocket, int | None]] = defaultdict(dict)

    def connect(self, room: Hashable, websocket: WebSocket, user_id: int | None = None) -> None:
        self._rooms[room][websocket] = user_id

    def disconnect(self, room: Hashable, websocket: WebSocket) -> None:
        connections = self._rooms.get(room)
        if connections is None:
            return
        connections.pop(websocket, None)
        if not connections:
            del self._rooms[room]

    def is_user_connected(self, room: Hashable, user_id: int) -> bool:
        return user_id in self._rooms.get(room, {}).values()

    def count_users(self, room: Hashable) -> int:
        """Количество уникальных зрителей: пользователь с несколькими вкладками считается один раз,
        каждое анонимное подключение — отдельно."""
        user_ids = self._rooms.get(room, {}).values()
        authenticated = {user_id for user_id in user_ids if user_id is not None}
        anonymous = sum(1 for user_id in user_ids if user_id is None)
        return len(authenticated) + anonymous

    async def broadcast(self, room: Hashable, payload: dict[str, Any]) -> None:
        for websocket in list(self._rooms.get(room, {})):
            try:
                await websocket.send_json(payload)
            except Exception:
                logger.warning("Не удалось отправить сообщение по WebSocket, подключение удалено")
                self.disconnect(room, websocket)


chat_manager = ConnectionManager()
property_viewers_manager = ConnectionManager()
