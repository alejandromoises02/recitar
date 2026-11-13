"""Reading and writing events. The table is described once, here; migrations create it."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import Column, ColumnElement, Connection, DateTime, MetaData, Table, Text, and_, func, select, tuple_
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB, insert

from app.domain.event import Event, EventCategory, ShowDate

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
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
)

# How a list of events is ordered: by start time (soonest first) or by announcement (first_seen_at,
# newest first). Ties go by id, ascending for starts_at and descending for announced.
EventSort = Literal["starts_at", "announced"]

# The last event already seen in that order: (starts_at or first_seen_at, id).
Position = tuple[datetime, str]


def upsert_events(connection: Connection, items: list[Event]) -> None:
    """Insert new events and update the ones already stored (same id)."""
    if not items:
        return
    rows = [item.model_dump(mode="json") for item in items]
    statement = insert(events).values(rows)
    # first_seen_at is kept from the first time the event was stored, so it is never updated.
    changes = {
        c.name: statement.excluded[c.name]
        for c in events.columns
        if not c.primary_key and c.name != "first_seen_at"
    }
    connection.execute(statement.on_conflict_do_update(index_elements=[events.c.id], set_=changes))


def count_upcoming_by_source(connection: Connection, now: datetime) -> dict[str, int]:
    """Stored events that have not happened yet, per source (the first part of the id)."""
    source = func.split_part(events.c.id, "-", 1)
    rows = connection.execute(select(source, func.count()).where(events.c.starts_at >= now).group_by(source))
    return {name: count for name, count in rows}


def list_events(connection: Connection) -> list[Event]:
    rows = connection.execute(select(events).order_by(events.c.starts_at, events.c.id)).mappings()
    return [Event.model_validate(dict(row)) for row in rows]


@dataclass(frozen=True)
class EventFilters:
    q: str | None = None  # words that must all appear in the title, artist or venue, ignoring case and accents
    starts_from: datetime | None = None  # included
    starts_before: datetime | None = None  # excluded
    venue: str | None = None  # exact name, as GET /venues lists it
    category: EventCategory | None = None
    announced_from: datetime | None = None  # first seen at or after this instant


def _folded(value: ColumnElement) -> ColumnElement:
    """Lower case without accents; f_unaccent comes from migration 0002."""
    return func.lower(func.f_unaccent(value))


def _escape_like(word: str) -> str:
    return word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _search(q: str) -> ColumnElement[bool]:
    text = _folded(func.concat_ws(" ", events.c.title, events.c.artist, events.c.venue))
    return and_(*(text.like(func.concat("%", _folded(_escape_like(word)), "%"), escape="\\") for word in q.split()))


def list_upcoming(
    connection: Connection,
    now: datetime,
    limit: int,
    after: Position | None,
    filters: EventFilters = EventFilters(),
    sort: EventSort = "starts_at",
) -> list[Event]:
    """Events from `now` on, in `sort` order, `limit` at a time.

    `after` is the position of the last event already seen, in the same order. Paging by that key
    instead of by offset means no event is repeated or skipped when new ones are stored between two
    pages.
    """
    query = select(events).where(events.c.starts_at >= now)
    if filters.q:
        query = query.where(_search(filters.q))
    if filters.starts_from is not None:
        query = query.where(events.c.starts_at >= filters.starts_from)
    if filters.starts_before is not None:
        query = query.where(events.c.starts_at < filters.starts_before)
    if filters.venue is not None:
        query = query.where(events.c.venue == filters.venue)
    if filters.category is not None:
        query = query.where(events.c.category == filters.category)
    if filters.announced_from is not None:
        query = query.where(events.c.first_seen_at >= filters.announced_from)
    if sort == "announced":
        if after is not None:
            query = query.where(tuple_(events.c.first_seen_at, events.c.id) < tuple_(*after))
        query = query.order_by(events.c.first_seen_at.desc(), events.c.id.desc())
    else:
        if after is not None:
            query = query.where(tuple_(events.c.starts_at, events.c.id) > tuple_(*after))
        query = query.order_by(events.c.starts_at, events.c.id)
    query = query.limit(limit)
    return [Event.model_validate(dict(row)) for row in connection.execute(query).mappings()]


def get_event(connection: Connection, event_id: str) -> Event | None:
    row = connection.execute(select(events).where(events.c.id == event_id)).mappings().one_or_none()
    return None if row is None else Event.model_validate(dict(row))


_DATE_SUFFIX = r"-\d{8}T\d{4}$"


def list_show_dates(connection: Connection, show: str, now: datetime) -> list[ShowDate]:
    """Upcoming dates of one show (see `show_key`). The key is compared whole, so
    `colon-el-cascanueces` never picks up `colon-el-cascanueces-2`."""
    key = func.regexp_replace(events.c.id, _DATE_SUFFIX, "")
    query = (
        select(events.c.id, events.c.starts_at)
        .where(key == show, events.c.starts_at >= now)
        .order_by(events.c.starts_at, events.c.id)
    )
    return [ShowDate(id=row.id, starts_at=row.starts_at) for row in connection.execute(query)]


class VenueCount(BaseModel):
    name: str  # what to send as `venue=` to GET /events
    upcoming_events: int


def list_upcoming_venues(connection: Connection, now: datetime) -> list[VenueCount]:
    """Venues with at least one event from `now` on, by name, with how many they have."""
    query = (
        select(events.c.venue, func.count())
        .where(events.c.starts_at >= now)
        .group_by(events.c.venue)
        .order_by(events.c.venue)
    )
    return [VenueCount(name=name, upcoming_events=count) for name, count in connection.execute(query)]
