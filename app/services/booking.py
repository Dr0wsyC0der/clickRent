from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.models.bookings import Booking as BookingModel
from app.exceptions.booking import PropertyNotFoundException, BookingConflictException, InvalidBookingDatesException
from datetime import date
class BookingService:
    def __init__(self, booking_repository: BookingRepository, property_repository: PropertyRepository):
        self.booking_repository = booking_repository
        self.property_repository = property_repository

    async def create_booking(self, user_id: int, property_id: int, check_in: date, check_out: date) -> BookingModel:
        if await self.property_repository.get_by_id(property_id) is None:
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
            status="pending"
        )

        return await self.booking_repository.create(new_booking)