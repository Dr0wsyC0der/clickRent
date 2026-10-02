from datetime import date, datetime, timedelta, timezone

from app.repositories.property import PropertyRepository
from app.repositories.property_view import PropertyViewRepository
from app.repositories.favorite import FavoriteRepository
from app.repositories.booking import BookingRepository
from app.schemas.property_signal import PropertySignalsResponse
from app.websocket.manager import ConnectionManager
from app.exceptions.property import PropertyNotFoundException

SIGNALS_WINDOW_DAYS = 7


class PropertySignalService:
    """Социальные сигналы объекта: кто смотрит сейчас и насколько объект востребован."""

    def __init__(
        self,
        property_repository: PropertyRepository,
        property_view_repository: PropertyViewRepository,
        favorite_repository: FavoriteRepository,
        booking_repository: BookingRepository,
        viewers_manager: ConnectionManager,
    ):
        self.property_repository = property_repository
        self.property_view_repository = property_view_repository
        self.favorite_repository = favorite_repository
        self.booking_repository = booking_repository
        self.viewers_manager = viewers_manager

    async def get_signals(self, property_id: int) -> PropertySignalsResponse:
        await self._ensure_property_exists(property_id)

        today = date.today()
        views_today = await self.property_view_repository.count_property_views_since(property_id, today)
        views_last_week = await self.property_view_repository.count_property_views_since(
            property_id, today - timedelta(days=SIGNALS_WINDOW_DAYS - 1)
        )
        favorites_count = await self.favorite_repository.count_by_property(property_id)
        bookings_last_week, last_booked_at = await self.booking_repository.get_property_booking_stats(
            property_id, datetime.now(timezone.utc) - timedelta(days=SIGNALS_WINDOW_DAYS)
        )

        return PropertySignalsResponse(
            property_id=property_id,
            viewing_now=await self.get_viewers_count(property_id),
            views_today=views_today,
            views_last_week=views_last_week,
            favorites_count=favorites_count,
            bookings_last_week=bookings_last_week,
            last_booked_at=last_booked_at,
        )

    async def authorize_watching(self, property_id: int) -> None:
        await self._ensure_property_exists(property_id)
        # Завершаем читающую транзакцию, чтобы WebSocket-подключение не держало ее открытой
        await self.property_repository.commit()

    async def get_viewers_count(self, property_id: int) -> int:
        return await self.viewers_manager.count_users(property_id)

    async def broadcast_viewers_count(self, property_id: int) -> None:
        await self.viewers_manager.broadcast(property_id, {
            "type": "viewers",
            "property_id": property_id,
            "count": await self.get_viewers_count(property_id),
        })

    async def _ensure_property_exists(self, property_id: int) -> None:
        if await self.property_repository.get_by_id(property_id) is None:
            raise PropertyNotFoundException("Недвижимость с указанным ID не найдена.")
