from sqlalchemy import String, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base
from app.db.enums import NotificationType

class Notification(Base, TimestampMixin, IDMixin):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped["NotificationType"] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")

    user: Mapped["User"] = relationship("User", back_populates="notifications")