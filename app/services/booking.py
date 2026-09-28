from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.models.bookings import Booking as BookingModel
from app.db.enums import BookingStatus
from app.exceptions.booking import PropertyNotFoundException, BookingConflictException, InvalidBookingDatesException, BookingNotFoundException, BookingAccessDeniedException, BookingStatusException
from datetime import datetime
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

    async def create_booking(self, user_id: int, property_id: int, check_in: datetime, check_out: datetime) -> BookingModel:
        booking_property = await self.property_repository.get_by_id(property_id)
        if booking_property is None:
            raise PropertyNotFoundException("Недействительный идентификатор объекта недвижимости.")
        if check_in >= check_out:
            raise InvalidBookingDatesException("Дата заезда должна быть раньше даты выезда.")
        has_overlap = await self.booking_repository.has_intersection(property_id, check_in, check_out)
        if has_overlap:
            raise BookingConflictException("Выбранные даты пересекаются с существующим бронированием.")

        new_booking = BookingModel(
            guest_id=user_id,
            property_id=property_id,
            check_in=check_in,
            check_out=check_out,
            total_price=booking_property.price_per_night * (check_out - check_in).days,
            status=BookingStatus.PENDING
        )

        new_booking = await self.booking_repository.create(new_booking)

        await self.notification_service.create_notification(
            user_id=booking_property.owner_id,
            notification_type=NotificationType.BOOKING_CREATED,
            title="Новое бронирование",
            message=f"Поступило новое бронирование объекта «{booking_property.title}».",
        )

        return new_booking

    async def cancel_booking(self, booking_id: int, user_id: int) -> None:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        if booking.guest_id != user_id:
            raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        if booking.status == BookingStatus.CANCELLED or booking.status == BookingStatus.COMPLETED:
            raise BookingStatusException("Менять статус бронирования на отмененный невозможно, так как оно уже завершено или отменено.")
        booking_property = await self.property_repository.get_by_id(booking.property_id)

        await self.booking_repository.cancel_booking(booking_id)

        await self.notification_service.create_notification(
            user_id=booking_property.owner_id,
            notification_type=NotificationType.BOOKING_CANCELLED,
            title="Бронирование отменено",
            message=f"Бронирование объекта «{booking_property.title}» было отменено.",
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

        await self.booking_repository.confirm_booking(booking_id)

        await self.notification_service.create_notification(
            user_id=booking.guest_id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Бронирование подтверждено",
            message=f"Ваше бронирование объекта «{booking_property.title}» подтверждено.",
        )

    async def get_user_bookings(self,user_id: int,page: int,size: int,) -> tuple[list[BookingModel], int]:
        return await self.booking_repository.get_user_bookings(
            user_id=user_id,
            page=page,
            size=size,
        )

    async def get_booking_by_id(self, booking_id: int, user_id: int) -> BookingModel:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        if booking.guest_id != user_id:
            raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        return booking

    async def get_all_bookings(self) -> List[BookingModel]:
        return await self.booking_repository.get_all_bookings()