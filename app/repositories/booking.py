from sqlalchemy import select, and_
from datetime import datetime
from app.models.bookings import Booking as BookingModel
from typing import List
from app.repositories.base import BaseRepository
from app.db.enums import BookingStatus

class BookingRepository(BaseRepository):
    async def create(self, booking: BookingModel) -> BookingModel:
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def get_user_bookings(self, user_id: int) -> List[BookingModel]:
        result = await self.session.scalars(select(BookingModel).where(BookingModel.guest_id == user_id))
        return result.all()

    async def get_property_bookings(self, property_id: int) -> List[BookingModel]:
        result = await self.session.scalars(select(BookingModel).where(BookingModel.property_id == property_id))
        return result.all()
    
    async def has_intersection(self, property_id: int, check_in: datetime, check_out: datetime) -> bool:
        result = await self.session.scalars(
            select(BookingModel).where(
                and_(
                    BookingModel.property_id == property_id,
                    BookingModel.check_in < check_out,
                    BookingModel.check_out > check_in,
                    BookingModel.status.in_([
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                    ])
                )
            )
        )
        return result.first() is not None
