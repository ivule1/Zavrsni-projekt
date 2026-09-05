"""Faza 9 (dopuna) - zakazano otvaranje/zatvaranje izbora.

Dodaje scheduled_open_at/scheduled_close_at na elections - koristi ih
pozadinski zadatak (app/scheduler.py) da automatski otvori/zatvori izbor u
zakazano vrijeme, bez potrebe da administrator rucno klikne bas u tom
trenutku (npr. "otvori u nedjelju u 7 ujutro, zatvori u 19").

Revision ID: f3a9c7e21b4d
Revises: d70a294c8d77
Create Date: 2026-09-04
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f3a9c7e21b4d"
down_revision = "d70a294c8d77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("elections", sa.Column("scheduled_open_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("elections", sa.Column("scheduled_close_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("elections", "scheduled_close_at")
    op.drop_column("elections", "scheduled_open_at")
