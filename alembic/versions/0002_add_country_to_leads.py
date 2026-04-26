"""add country to leads

Revision ID: 0002_add_country_to_leads
Revises: 0001_initial_schema
Create Date: 2026-04-26 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_country_to_leads"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("country", sa.String(length=2), nullable=True))
    op.execute("UPDATE leads SET country = 'XX' WHERE country IS NULL")
    op.alter_column("leads", "country", nullable=False)


def downgrade() -> None:
    op.drop_column("leads", "country")
