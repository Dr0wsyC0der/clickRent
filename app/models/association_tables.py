from sqlalchemy import Table, Column, ForeignKey

from app.db.base import Base

property_amenities = Table(
    "property_amenities",
    Base.metadata,
    Column(
        "property_id",
        ForeignKey("properties.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "amenity_id",
        ForeignKey("amenities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)