"""Исправил уникальность просмотров для пользователей и гостей

Revision ID: 893c74b5c490
Revises: 932250fbfc82
Create Date: 2026-09-30 12:29:19.555205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '893c74b5c490'
down_revision: Union[str, Sequence[str], None] = '932250fbfc82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_property_view_user_property_date",
        "property_views",
        type_="unique"
    )

    op.add_column(
        "property_views",
        sa.Column("visitor_id", sa.UUID(), nullable=True)
    )

    op.create_check_constraint(
        "ck_property_view_exactly_one_owner",
        "property_views",
        "(user_id IS NOT NULL) <> (visitor_id IS NOT NULL)"
    )

    op.create_index(
        "uq_property_view_user_property_date",
        "property_views",
        ["user_id", "property_id", "view_date"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL")
    )

    op.create_index(
        "uq_property_view_visitor_property_date",
        "property_views",
        ["visitor_id", "property_id", "view_date"],
        unique=True,
        postgresql_where=sa.text("visitor_id IS NOT NULL")
    )

def downgrade() -> None:
    op.drop_index(
        "uq_property_view_visitor_property_date",
        table_name="property_views"
    )

    op.drop_index(
        "uq_property_view_user_property_date",
        table_name="property_views"
    )

    op.drop_constraint(
        "ck_property_view_exactly_one_owner",
        "property_views",
        type_="check"
    )

    op.drop_column(
        "property_views",
        "visitor_id"
    )

    op.create_unique_constraint(
        "uq_property_view_user_property_date",
        "property_views",
        ["user_id", "property_id", "view_date"]
    )