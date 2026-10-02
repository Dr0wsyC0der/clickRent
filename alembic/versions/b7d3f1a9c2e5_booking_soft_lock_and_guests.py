"""Добавил soft-lock бронирований и количество гостей

Revision ID: b7d3f1a9c2e5
Revises: a1c5e7d2b904
Create Date: 2026-10-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d3f1a9c2e5'
down_revision: Union[str, Sequence[str], None] = 'a1c5e7d2b904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'EXPIRED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BOOKING_EXPIRED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BOOKING_COMPLETED'")

    op.add_column(
        "bookings",
        sa.Column("guests", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "bookings",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "check_booking_guests",
        "bookings",
        "guests > 0",
    )


def downgrade() -> None:
    op.drop_constraint("check_booking_guests", "bookings", type_="check")
    op.drop_column("bookings", "expires_at")
    op.drop_column("bookings", "guests")

    # Значения enum в PostgreSQL удалить нельзя без пересоздания типа, поэтому они остаются.
