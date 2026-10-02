import asyncio
import logging
import os
import socket

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.redis import redis_key
from app.repositories.booking import BookingRepository
from app.repositories.notification import NotificationRepository
from app.repositories.property import PropertyRepository
from app.services.booking import BookingService
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)

MAINTENANCE_LOCK_KEY = redis_key("lock", "booking-maintenance")


async def process_bookings(session_maker: async_sessionmaker[AsyncSession]) -> tuple[int, int]:
    async with session_maker() as session:
        service = BookingService(
            booking_repository=BookingRepository(session),
            property_repository=PropertyRepository(session),
            notification_service=NotificationService(NotificationRepository(session)),
        )
        expired = await service.expire_pending_bookings()
        completed = await service.complete_finished_bookings()

    if expired or completed:
        logger.info("Обработаны бронирования: истекло %s, завершено %s", expired, completed)

    return expired, completed


async def acquire_maintenance_slot(redis: Redis, ttl_seconds: int) -> bool:
    """Распределенный лок на один запуск: из всех воркеров и инстансов задачу за период выполняет один.

    Лок не снимается после выполнения и истекает сам через период, поэтому обработка идет
    примерно раз в `ttl_seconds` на весь кластер. Если Redis недоступен, задача выполняется:
    переходы статусов атомарны (UPDATE ... WHERE status = ... RETURNING), повторный запуск
    в другом воркере не создаст дублей, только лишнюю работу.
    """
    owner = f"{socket.gethostname()}:{os.getpid()}"
    try:
        return bool(await redis.set(MAINTENANCE_LOCK_KEY, owner, nx=True, ex=ttl_seconds))
    except Exception:
        logger.warning("Redis недоступен, фоновая обработка бронирований выполняется без лока", exc_info=True)
        return True


async def run_booking_maintenance(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    interval_seconds: int,
) -> None:
    """Периодически снимает истекшие soft-lock и завершает прошедшие проживания."""
    while True:
        try:
            if await acquire_maintenance_slot(redis, interval_seconds):
                await process_bookings(session_maker)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка фоновой обработки бронирований")

        await asyncio.sleep(interval_seconds)
