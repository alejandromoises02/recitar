"""featured_shows: shows picked by hand for the home, in order (written by PUT /featured).

Revision ID: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "featured_shows",
        sa.Column("show_key", sa.Text, primary_key=True),  # an event id without its date (see show_key)
        sa.Column("position", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("featured_shows")
