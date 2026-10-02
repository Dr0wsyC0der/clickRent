"""Синхронизировал схему с моделями: enum уведомлений и анонимные просмотры

Revision ID: a1c5e7d2b904
Revises: 893c74b5c490
Create Date: 2026-10-02 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c5e7d2b904'
down_revision: Union[str, Sequence[str], None] = '893c74b5c490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BOOKING_CANCELLED'")

    op.alter_column(
        "property_views",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.create_index(
        "ix_property_views_visitor_id",
        "property_views",
        ["visitor_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_property_views_visitor_id",
        table_name="property_views",
    )

    op.alter_column(
        "property_views",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Значение enum в PostgreSQL удалить нельзя без пересоздания типа, поэтому оно остается.
