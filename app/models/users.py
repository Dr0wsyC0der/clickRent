from sqlalchemy import Boolean, String, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List


from app.db.enums import UserRole
from app.db.base import Base
from app.db.mixins import TimestampMixin, IDMixin



class User(Base, TimestampMixin, IDMixin):  
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)

    # Relationships
    properties: Mapped[List["Property"]] = relationship("Property", back_populates="owner")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="guest")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="author")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="sender")
    chat_participants: Mapped[List["ChatParticipant"]] = relationship("ChatParticipant", back_populates="user")
    views: Mapped[List["PropertyView"]] = relationship("PropertyView", back_populates="user")