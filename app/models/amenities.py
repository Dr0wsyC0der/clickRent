from sqlalchemy import  String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List

from app.db.base import Base
from app.db.mixins import IDMixin

class Amenity(Base, IDMixin):
    __tablename__ = "amenities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)

    properties: Mapped[List["Property"]] = relationship("Property", secondary="property_amenities", back_populates="amenities")