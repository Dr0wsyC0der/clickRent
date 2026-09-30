"""Добавил уникальность просмотров недвижимости за день

Revision ID: 932250fbfc82
Revises: 9f5d648d5714
Create Date: 2026-09-30 12:12:13.927268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '932250fbfc82'
down_revision: Union[str, Sequence[str], None] = '9f5d648d5714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "property_views",
        sa.Column("view_date", sa.Date(), nullable=True)
    )

    op.execute("""
        UPDATE property_views
        SET view_date = DATE(created_at)
    """)

    op.alter_column(
        "property_views",
        "view_date",
        nullable=False
    )

    op.create_unique_constraint(
        "uq_property_view_user_property_date",
        "property_views",
        ["user_id", "property_id", "view_date"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_property_view_user_property_date",
        "property_views",
        type_="unique"
    )

    op.drop_column(
        "property_views",
        "view_date"
    )