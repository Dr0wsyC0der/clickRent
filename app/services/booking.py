from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.models.bookings import Booking as BookingModel
from app.exceptions.booking import PropertyNotFoundException, BookingConflictException, InvalidBookingDatesException, BookingNotFoundException, BookingAccessDeniedException, BookingStatusException, BookingCapacityException
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import List
from app.services.notification import NotificationService
from app.db.enums import BookingStatus, NotificationType
class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        property_repository: PropertyRepository,
        notification_service: NotificationService,
    ):
        self.booking_repository = booking_repository
        self.property_repository = property_repository
        self.notification_service = notification_service

    async def create_booking(self, user_id: int, property_id: int, check_in: datetime, check_out: datetime, guests: int = 1) -> BookingModel:
        now = datetime.now(timezone.utc)
        if check_in >= check_out:
            raise InvalidBookingDatesException("Дата заезда должна быть раньше даты выезда.")
        nights = (check_out - check_in).days
        if nights < 1:
            raise InvalidBookingDatesException("Минимальный срок бронирования — одна ночь.")
        if check_in < now:
            raise InvalidBookingDatesException("Нельзя забронировать даты в прошлом.")

        # Блокируем объект до коммита: параллельный запрос на те же даты дождется
        # окончания этой транзакции и увидит созданную бронь при проверке пересечений
        booking_property = await self.property_repository.get_by_id_for_update(property_id)
        if booking_property is None:
            raise PropertyNotFoundException("Недействительный идентификатор объекта недвижимости.")
        if guests > booking_property.guest_capacity:
            raise BookingCapacityException(
                f"Объект вмещает не более {booking_property.guest_capacity} гостей."
            )
        has_overlap = await self.booking_repository.has_intersection(property_id, check_in, check_out)
        if has_overlap:
            raise BookingConflictException("Выбранные даты пересекаются с существующим бронированием.")

        new_booking = BookingModel(
            guest_id=user_id,
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            total_price=booking_property.price_per_night * nights,
            status=BookingStatus.PENDING,
            expires_at=now + timedelta(minutes=settings.booking_pending_ttl_minutes),
        )

        new_booking = await self.booking_repository.create(new_booking)

        await self.notification_service.create_notification(
            user_id=booking_property.owner_id,
            notification_type=NotificationType.BOOKING_CREATED,
            title="Новое бронирование",
            message=f"Поступило новое бронирование №{new_booking.id} объекта «{booking_property.title}».",
        )

        return new_booking

    async def cancel_booking(self, booking_id: int, user_id: int) -> None:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        booking_property = await self.property_repository.get_by_id(booking.property_id)
        is_guest = booking.guest_id == user_id
        is_owner = booking_property is not None and booking_property.owner_id == user_id
        if not is_guest and not is_owner:
            raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise BookingStatusException("Менять статус бронирования на отмененный невозможно, так как оно уже завершено или отменено.")
        if booking.status == BookingStatus.CONFIRMED and booking.check_in <= datetime.now(timezone.utc):
            raise BookingStatusException("Нельзя отменить бронирование после даты заезда.")

        cancelled = await self.booking_repository.cancel_booking(booking_id)
        if not cancelled:
            raise BookingStatusException("Статус бронирования уже изменился, отмена невозможна.")

        if is_guest:
            await self.notification_service.create_notification(
                user_id=booking_property.owner_id,
                notification_type=NotificationType.BOOKING_CANCELLED,
                title="Бронирование отменено",
                message=f"Бронирование №{booking.id} объекта «{booking_property.title}» было отменено.",
            )
        else:
            await self.notification_service.create_notification(
                user_id=booking.guest_id,
                notification_type=NotificationType.BOOKING_CANCELLED,
                title="Бронирование отклонено",
                message=f"Владелец отклонил ваше бронирование №{booking.id} объекта «{booking_property.title}».",
            )

    async def confirm_booking(self,booking_id: int,user_id: int,) -> None:
        booking = await self.booking_repository.get_booking_by_id(
            booking_id
        )

        if booking is None:
            raise BookingNotFoundException(
                "Бронирование с указанным идентификатором не найдено."
            )

        booking_property = await self.property_repository.get_by_id(
            booking.property_id
        )

        if booking_property is None:
            raise PropertyNotFoundException(
                "Недвижимость, связанная с бронированием, не найдена."
            )

        if booking_property.owner_id != user_id:
            raise BookingAccessDeniedException(
                "Только владелец недвижимости может подтвердить бронирование."
            )

        if booking.status != BookingStatus.PENDING:
            raise BookingStatusException(
                "Подтвердить можно только ожидающее бронирование."
            )

        now = datetime.now(timezone.utc)
        if booking.expires_at is not None and booking.expires_at <= now:
            raise BookingStatusException(
                "Время ожидания подтверждения истекло, даты снова доступны для бронирования."
            )

        confirmed = await self.booking_repository.confirm_booking(booking_id, now)
        if not confirmed:
            raise BookingStatusException(
                "Статус бронирования уже изменился, подтверждение невозможно."
            )

        await self.notification_service.create_notification(
            user_id=booking.guest_id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Бронирование подтверждено",
            message=f"Ваше бронирование объекта «{booking_property.title}» подтверждено.",
        )

    async def expire_pending_bookings(self) -> int:
        expired = await self.booking_repository.expire_pending_bookings(datetime.now(timezone.utc))
        for booking in expired:
            await self.notification_service.create_notification(
                user_id=booking.guest_id,
                notification_type=NotificationType.BOOKING_EXPIRED,
                title="Бронирование истекло",
                message=f"Владелец не подтвердил бронирование №{booking.id} вовремя, даты снова доступны.",
            )
        return len(expired)

    async def complete_finished_bookings(self) -> int:
        completed = await self.booking_repository.complete_finished_bookings(datetime.now(timezone.utc))
        for booking in completed:
            await self.notification_service.create_notification(
                user_id=booking.guest_id,
                notification_type=NotificationType.BOOKING_COMPLETED,
                title="Проживание завершено",
                message=f"Проживание по бронированию №{booking.id} завершено. Оставьте отзыв об объекте!",
            )
        return len(completed)

    async def get_user_bookings(self,user_id: int,page: int,size: int,) -> tuple[list[BookingModel], int]:
        return await self.booking_repository.get_user_bookings(
            user_id=user_id,
            page=page,
            size=size,
        )

    async def get_host_bookings(self, owner_id: int, page: int, size: int, status: BookingStatus | None = None) -> tuple[list[BookingModel], int]:
        return await self.booking_repository.get_host_bookings(
            owner_id=owner_id,
            page=page,
            size=size,
            status=status,
        )

    async def get_booking_by_id(self, booking_id: int, user_id: int) -> BookingModel:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        if booking.guest_id != user_id:
            booking_property = await self.property_repository.get_by_id(booking.property_id)
            if booking_property is None or booking_property.owner_id != user_id:
                raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        return booking

    async def get_all_bookings(self) -> List[BookingModel]:
        return await self.booking_repository.get_all_bookings()
