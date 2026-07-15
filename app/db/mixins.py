from sqlalchemy import DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class IDMixin:
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )