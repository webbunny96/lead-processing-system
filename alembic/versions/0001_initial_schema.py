"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-24 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "affiliates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("token_sub", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_affiliates_id", "affiliates", ["id"], unique=False)
    op.create_index("ix_affiliates_token_sub", "affiliates", ["token_sub"], unique=True)

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["affiliate_id"], ["affiliates.id"]),
    )
    op.create_index("ix_offers_id", "offers", ["id"], unique=False)
    op.create_index("ix_offers_affiliate_id", "offers", ["affiliate_id"], unique=False)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["affiliate_id"], ["affiliates.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
    )
    op.create_index("ix_leads_id", "leads", ["id"], unique=False)
    op.create_index("ix_leads_affiliate_id", "leads", ["affiliate_id"], unique=False)
    op.create_index("ix_leads_offer_id", "leads", ["offer_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_leads_offer_id", table_name="leads")
    op.drop_index("ix_leads_affiliate_id", table_name="leads")
    op.drop_index("ix_leads_id", table_name="leads")
    op.drop_table("leads")

    op.drop_index("ix_offers_affiliate_id", table_name="offers")
    op.drop_index("ix_offers_id", table_name="offers")
    op.drop_table("offers")

    op.drop_index("ix_affiliates_token_sub", table_name="affiliates")
    op.drop_index("ix_affiliates_id", table_name="affiliates")
    op.drop_table("affiliates")
