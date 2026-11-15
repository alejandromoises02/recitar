"""ticket_clicks: one row per click on a ticket button that went through GET /go/{event_id}.

Only what the count needs: the show, the date, the ticketer, where in the app and when. No IP, no user
agent, no person. `show_key` is not a foreign key so the count stays when an event is dropped.

Revision ID: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_clicks",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("show_key", sa.Text, nullable=False),
        sa.Column("event_id", sa.Text, nullable=False),
        sa.Column("vendor", sa.Text),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_clicks")
