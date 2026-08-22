from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.models.bookings import Booking as BookingModel
from app.db.enums import BookingStatus
from app.exceptions.booking import PropertyNotFoundException, BookingConflictException, InvalidBookingDatesException, BookingNotFoundException, BookingAccessDeniedException, BookingStatusException
from datetime import datetime
from typing import List
class BookingService:
    def __init__(self, booking_repository: BookingRepository, property_repository: PropertyRepository):
        self.booking_repository = booking_repository
        self.property_repository = property_repository

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

        return await self.booking_repository.create(new_booking)

    async def cancel_booking(self, booking_id: int, user_id: int) -> None:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        if booking.guest_id != user_id:
            raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        if booking.status == BookingStatus.CANCELLED or booking.status == BookingStatus.COMPLETED:
            raise BookingStatusException("Менять статус бронирования на отмененный невозможно, так как оно уже завершено или отменено.")
        await self.booking_repository.cancel_booking(booking_id)

    async def get_user_bookings(self, user_id: int) -> List[BookingModel]:
        return await self.booking_repository.get_user_bookings(user_id)

    async def get_booking_by_id(self, booking_id: int, user_id: int) -> BookingModel:
        booking = await self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException("Бронирование с указанным идентификатором не найдено.")
        if booking.guest_id != user_id:
            raise BookingAccessDeniedException("У вас нет доступа к этому бронированию.")
        return booking

    async def get_all_bookings(self) -> List[BookingModel]:
        return await self.booking_repository.get_all_bookings()