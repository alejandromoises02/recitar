"""Reading and writing events. The table is described once, here; migrations create it."""

from datetime import datetime

from sqlalchemy import Column, Connection, DateTime, MetaData, Table, Text, func, select, tuple_
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


def count_upcoming_by_source(connection: Connection, now: datetime) -> dict[str, int]:
    """Stored events that have not happened yet, per source (the first part of the id)."""
    source = func.split_part(events.c.id, "-", 1)
    rows = connection.execute(select(source, func.count()).where(events.c.starts_at >= now).group_by(source))
    return {name: count for name, count in rows}


def list_events(connection: Connection) -> list[Event]:
    rows = connection.execute(select(events).order_by(events.c.starts_at, events.c.id)).mappings()
    return [Event.model_validate(dict(row)) for row in rows]


def list_upcoming(
    connection: Connection, now: datetime, limit: int, after: tuple[datetime, str] | None
) -> list[Event]:
    """Events from `now` on, by start time then id, `limit` at a time.

    `after` is the (starts_at, id) of the last event already seen. Paging by that key instead of by
    offset means no event is repeated or skipped when new ones are stored between two pages.
    """
    query = select(events).where(events.c.starts_at >= now)
    if after is not None:
        query = query.where(tuple_(events.c.starts_at, events.c.id) > tuple_(*after))
    query = query.order_by(events.c.starts_at, events.c.id).limit(limit)
    return [Event.model_validate(dict(row)) for row in connection.execute(query).mappings()]
