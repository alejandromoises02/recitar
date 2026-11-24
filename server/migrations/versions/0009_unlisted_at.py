"""unlisted_at: when the event's source stopped listing it (a cancelled show leaves the listing).

An unlisted event is hidden, not deleted: listed again, it comes back. Events already stored start listed.

Revision ID: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("unlisted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "unlisted_at")
