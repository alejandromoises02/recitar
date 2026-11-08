"""create the events table

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("artist", sa.Text),
        sa.Column("venue", sa.Text, nullable=False),
        sa.Column("city", sa.Text),
        sa.Column("region", sa.Text),
        sa.Column("country", sa.Text),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticket_links", JSONB, nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("image_url", sa.Text),
        sa.Column("image_origin", sa.Text),
        sa.Column("image_author", sa.Text),
        sa.Column("image_license", sa.Text),
        sa.Column("image_source_url", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_starts_at", "events", ["starts_at"])


def downgrade() -> None:
    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_table("events")
