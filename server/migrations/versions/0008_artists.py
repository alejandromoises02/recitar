"""artists: one row per artist name we looked up on Spotify, apart from the events.

The key is the artist exactly as events.artist holds it, so linking the events needs no new column
and no event row is rewritten. It is not a foreign key: events.artist is filled at scrape time and an
artist row may outlive its events. spotify_id is null when Spotify had no artist of that name on
checked_at, so it is asked again only after a while.

Revision ID: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("name", sa.Text, primary_key=True),
        sa.Column("spotify_id", sa.Text),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("artists")
