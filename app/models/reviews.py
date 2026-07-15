from sqlalchemy import String, Numeric, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey
from decimal import Decimal

from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base

class Review(Base, TimestampMixin, IDMixin):
    __tablename__ = "reviews"
    __table_args__ = (
    CheckConstraint(
        "rating >= 1 AND rating <= 5",
        name="check_rating"
    ),
    )

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True, unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False) 
    comment: Mapped[str] = mapped_column(String(500), nullable=True)

    property: Mapped["Property"] = relationship("Property", back_populates="reviews")
    author: Mapped["User"] = relationship("User", back_populates="reviews")
    booking: Mapped["Booking"] = relationship("Booking", back_populates="reviews")