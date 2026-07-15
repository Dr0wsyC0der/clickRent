from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.db.base import Base

class Favorite(Base):
    __tablename__ = "favorites"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    property: Mapped["Property"] = relationship("Property", back_populates="favorites")
    user: Mapped["User"] = relationship("User", back_populates="favorites")