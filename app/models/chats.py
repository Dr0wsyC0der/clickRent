from sqlalchemy.orm import Mapped, relationship
from typing import List

from app.db.base import Base
from app.db.mixins import TimestampMixin, IDMixin

class Chat(Base, TimestampMixin, IDMixin):
    __tablename__ = "chats"

    messages: Mapped[List["Message"]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    participants: Mapped[List["ChatParticipant"]] = relationship("ChatParticipant", back_populates="chat", cascade="all, delete-orphan")