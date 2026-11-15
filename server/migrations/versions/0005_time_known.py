"""time_known: False when the source gave only the day of an event, not its time.

Events already stored are marked known: the next scrape corrects the few that came without a time.

Revision ID: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The default fills the existing rows; it is dropped right after so the app is the only writer.
    op.add_column("events", sa.Column("time_known", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column("events", "time_known", server_default=None)


def downgrade() -> None:
    op.drop_column("events", "time_known")
