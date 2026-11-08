"""Reading and writing events. The table is described once, here; migrations create it."""

from sqlalchemy import Column, Connection, DateTime, MetaData, Table, Text, select
from sqlalchemy.dialects.postgresql import JSONB, insert

from app.domain.event import Event

metadata = MetaData()

events = Table(
    "events",
    metadata,
    Column("id", Text, primary_key=True),
    Column("category", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("artist", Text),
    Column("venue", Text, nullable=False),
    Column("city", Text),
    Column("region", Text),
    Column("country", Text),
    Column("starts_at", DateTime(timezone=True), nullable=False),
    Column("ticket_links", JSONB, nullable=False),
    Column("source_url", Text, nullable=False),
    Column("image_url", Text),
    Column("image_origin", Text),
    Column("image_author", Text),
    Column("image_license", Text),
    Column("image_source_url", Text),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def upsert_events(connection: Connection, items: list[Event]) -> None:
    """Insert new events and update the ones already stored (same id)."""
    if not items:
        return
    rows = [item.model_dump(mode="json") for item in items]
    statement = insert(events).values(rows)
    changes = {c.name: statement.excluded[c.name] for c in events.columns if not c.primary_key}
    connection.execute(statement.on_conflict_do_update(index_elements=[events.c.id], set_=changes))


def list_events(connection: Connection) -> list[Event]:
    rows = connection.execute(select(events).order_by(events.c.starts_at, events.c.id)).mappings()
    return [Event.model_validate(dict(row)) for row in rows]
