from sqlalchemy import select, and_, or_, update, func, ColumnElement
from datetime import datetime, timezone
from app.models.bookings import Booking as BookingModel
from app.models.properties import Property as PropertyModel
from typing import List
from app.repositories.base import BaseRepository
from app.db.enums import BookingStatus


def active_booking_condition(now: datetime) -> ColumnElement[bool]:
    """Бронь занимает даты, если она подтверждена или ожидает подтверждения и soft-lock еще не истек."""
    return or_(
        BookingModel.status == BookingStatus.CONFIRMED,
        and_(
            BookingModel.status == BookingStatus.PENDING,
            or_(
                BookingModel.expires_at.is_(None),
                BookingModel.expires_at > now,
            ),
        ),
    )


class BookingRepository(BaseRepository):
    async def create(self, booking: BookingModel) -> BookingModel:
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def cancel_booking(self, booking_id: int) -> bool:
        stmt = (
            update(BookingModel)
            .where(
                BookingModel.id == booking_id,
                BookingModel.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            )
            .values(status=BookingStatus.CANCELLED)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def confirm_booking(self, booking_id: int, now: datetime) -> bool:
        stmt = (
            update(BookingModel)
            .where(
                BookingModel.id == booking_id,
                BookingModel.status == BookingStatus.PENDING,
                or_(BookingModel.expires_at.is_(None), BookingModel.expires_at > now),
            )
            .values(status=BookingStatus.CONFIRMED, expires_at=None)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def expire_pending_bookings(self, now: datetime) -> list[BookingModel]:
        # UPDATE ... RETURNING атомарно забирает строки, поэтому при нескольких воркерах
        # каждая бронь будет обработана (и уведомление отправлено) ровно один раз
        result = await self.session.scalars(
            update(BookingModel)
            .where(
                BookingModel.status == BookingStatus.PENDING,
                BookingModel.expires_at <= now,
            )
            .values(status=BookingStatus.EXPIRED)
            .returning(BookingModel)
        )
        bookings = result.all()
        await self.session.commit()
        return bookings

    async def complete_finished_bookings(self, now: datetime) -> list[BookingModel]:
        result = await self.session.scalars(
            update(BookingModel)
            .where(
                BookingModel.status == BookingStatus.CONFIRMED,
                BookingModel.check_out <= now,
            )
            .values(status=BookingStatus.COMPLETED)
            .returning(BookingModel)
        )
        bookings = result.all()
        await self.session.commit()
        return bookings

    async def get_user_bookings(self,user_id: int,page: int,size: int,) -> tuple[list[BookingModel], int]:
        count_query = (select(func.count()).select_from(BookingModel).where(BookingModel.guest_id == user_id))
        total = await self.session.scalar(count_query)
        result = await self.session.scalars(
            select(BookingModel)
            .where(BookingModel.guest_id == user_id)
            .order_by(BookingModel.check_in.desc(), BookingModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        bookings = result.all()

        return bookings, total

    async def get_host_bookings(self, owner_id: int, page: int, size: int, status: BookingStatus | None = None) -> tuple[list[BookingModel], int]:
        conditions = [PropertyModel.owner_id == owner_id]
        if status is not None:
            conditions.append(BookingModel.status == status)

        total = await self.session.scalar(
            select(func.count())
            .select_from(BookingModel)
            .join(PropertyModel, PropertyModel.id == BookingModel.property_id)
            .where(*conditions)
        )
        result = await self.session.scalars(
            select(BookingModel)
            .join(PropertyModel, PropertyModel.id == BookingModel.property_id)
            .where(*conditions)
            .order_by(BookingModel.check_in.desc(), BookingModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        return result.all(), total

    async def get_all_bookings(self) -> List[BookingModel]:
        result = await self.session.scalars(select(BookingModel))
        return result.all()

    async def get_property_bookings(self, property_id: int) -> List[BookingModel]:
        result = await self.session.scalars(select(BookingModel).where(BookingModel.property_id == property_id))
        return result.all()

    async def has_intersection(self, property_id: int, check_in: datetime, check_out: datetime) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.session.scalars(
            select(BookingModel).where(
                and_(
                    BookingModel.property_id == property_id,
                    BookingModel.check_in < check_out,
                    BookingModel.check_out > check_in,
                    active_booking_condition(now),
                )
            )
        )
        return result.first() is not None

    async def get_booking_by_id(self, booking_id: int) -> BookingModel|None:
        result = await self.session.scalars(
            select(BookingModel)
            .where(BookingModel.id == booking_id)
            .execution_options(populate_existing=True)
        )
        return result.first()
