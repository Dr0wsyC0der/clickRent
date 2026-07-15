from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base


class PropertyView(Base, TimestampMixin, IDMixin):
    __tablename__ = "property_views"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)

    user: Mapped["User"] = relationship("User", back_populates="views")
    property: Mapped["Property"] = relationship("Property", back_populates="views")