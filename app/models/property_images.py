from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base

class PropertyImage(Base, TimestampMixin, IDMixin):
    __tablename__ = "property_images"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="images")