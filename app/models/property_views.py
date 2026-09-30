from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date
from sqlalchemy import ForeignKey, Date, CheckConstraint, UUID as SQLUUID, Index, text
from app.db.mixins import TimestampMixin, IDMixin
from app.db.base import Base
from uuid import UUID


class PropertyView(Base, TimestampMixin, IDMixin):
    __tablename__ = "property_views"

    user_id: Mapped[int|None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    visitor_id: Mapped[UUID | None] = mapped_column(SQLUUID(as_uuid=True),index=True, nullable=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    view_date: Mapped[date] = mapped_column(Date,nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL) <> (visitor_id IS NOT NULL)",
            name="ck_property_view_exactly_one_owner"
        ),
        Index(
            "uq_property_view_user_property_date",
            "user_id",
            "property_id",
            "view_date",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "uq_property_view_visitor_property_date",
            "visitor_id",
            "property_id",
            "view_date",
            unique=True,
            postgresql_where=text("visitor_id IS NOT NULL"),
        ),
)

    user: Mapped["User"] = relationship("User", back_populates="views")
    property: Mapped["Property"] = relationship("Property", back_populates="views")