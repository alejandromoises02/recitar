"""first_seen_at: when a scraper first read each event, for "just announced".

Events already stored get the time of this migration: when they were really first seen is unknown.

Revision ID: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The default fills the existing rows; it is dropped right after so the app is the only writer.
    op.add_column(
        "events",
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.alter_column("events", "first_seen_at", server_default=None)
    op.create_index("ix_events_first_seen_at_id", "events", ["first_seen_at", "id"])  # read backwards for announced


def downgrade() -> None:
    op.drop_index("ix_events_first_seen_at_id", table_name="events")
    op.drop_column("events", "first_seen_at")
