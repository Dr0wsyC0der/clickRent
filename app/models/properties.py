from sqlalchemy import Integer, String, Numeric, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
from decimal import Decimal

from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base


class Property(Base, TimestampMixin, IDMixin):
    __tablename__ = "properties"
    __table_args__ = (
    CheckConstraint(
        "beds > 0 AND bathrooms > 0 AND rooms > 0 AND guest_capacity > 0",
        name="check_property_values"
    ),
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=True)
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    beds: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    guest_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


    owner: Mapped["User"] = relationship("User", back_populates="properties")
    images: Mapped[List["PropertyImage"]] = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="property", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="property", cascade="all, delete-orphan")
    amenities: Mapped[List["Amenity"]] = relationship("Amenity", secondary="property_amenities", back_populates="properties")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="property", cascade="all, delete-orphan")
    views: Mapped[List["PropertyView"]] = relationship("PropertyView", back_populates="property", cascade="all, delete-orphan")

