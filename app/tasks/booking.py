import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.booking import BookingRepository
from app.repositories.notification import NotificationRepository
from app.repositories.property import PropertyRepository
from app.services.booking import BookingService
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


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


async def run_booking_maintenance(session_maker: async_sessionmaker[AsyncSession], interval_seconds: int) -> None:
    """Периодически снимает истекшие soft-lock и завершает прошедшие проживания."""
    while True:
        try:
            await process_bookings(session_maker)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка фоновой обработки бронирований")

        await asyncio.sleep(interval_seconds)
