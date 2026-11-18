"""venues: one row per venue with its address and coordinates, apart from the events.

The key is the venue's canonical name (app/scrapers/venues.py), the same name events.venue already
holds, so linking the events needs no new column and no event row is rewritten. ON UPDATE CASCADE
lets a venue be renamed in one place.

coords_source says where the coordinates came from: 'ticketer', 'osm' (geocoded) or 'manual'.

Revision ID: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "venues",
        sa.Column("name", sa.Text, primary_key=True),
        sa.Column("address", sa.Text),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("coords_source", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("coords_source IN ('ticketer', 'osm', 'manual')", name="ck_venues_coords_source"),
        sa.CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="ck_venues_both_coords"),
    )
    op.execute("INSERT INTO venues (name, updated_at) SELECT DISTINCT venue, now() FROM events")
    op.create_foreign_key(
        "fk_events_venue", "events", "venues", ["venue"], ["name"], onupdate="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_events_venue", "events", type_="foreignkey")
    op.drop_table("venues")
