from sqlalchemy import Numeric, DateTime, Enum, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from app.db.enums import BookingStatus
from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base

class Booking(Base, TimestampMixin, IDMixin):
    __tablename__ = "bookings"
    __table_args__ = (
    CheckConstraint(
        "check_out > check_in",
        name="check_booking_dates"
    ),
    )

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    guest_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    check_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    check_out: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="bookings")
    guest: Mapped["User"] = relationship("User", back_populates="bookings")
    review: Mapped["Review"] = relationship("Review", back_populates="booking", uselist=False, cascade="all, delete-orphan")