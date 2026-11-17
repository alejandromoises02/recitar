"""Reading and writing events. The table is described once, here; migrations create it."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import (
    BigInteger, Boolean, Column, ColumnElement, Connection, DateTime, Identity, Integer, MetaData, Row, Table, Text, and_, delete, func, select, tuple_,
)
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB, insert

from app.domain.event import Event, EventCategory, Show, ShowDate
from app.domain.ticket_redirect import TicketClick

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
    Column("time_known", Boolean, nullable=False),
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

featured_shows = Table(
    "featured_shows",
    metadata,
    Column("show_key", Text, primary_key=True),
    Column("position", Integer, nullable=False),
)

# One row per ticket click that went through GET /go/{event_id}: no IP, no user agent, no person.
# `show_key` is not a foreign key: the count outlives the event rows.
ticket_clicks = Table(
    "ticket_clicks",
    metadata,
    Column("id", BigInteger, Identity(), primary_key=True),
    Column("show_key", Text, nullable=False),
    Column("event_id", Text, nullable=False),
    Column("vendor", Text),
    Column("source", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# How a list of events is ordered: by start time (soonest first) or by announcement (first_seen_at,
# newest first). Ties go by id, ascending for starts_at and descending for announced.
EventSort = Literal["starts_at", "announced"]

# The last item already seen in that order: (starts_at or first_seen_at, id). For a show, starts_at
# is its next date and id is the show key.
Position = tuple[datetime, str]

# Event ids are `<source>-<show>-<YYYYMMDDTHHMM>`: without the date suffix they name the show (the
# same rule as domain.event.show_key, done in SQL).
_DATE_SUFFIX = r"-\d{8}T\d{4}$"
_show_key = func.regexp_replace(events.c.id, _DATE_SUFFIX, "")


def upsert_events(connection: Connection, items: list[Event]) -> None:
    """Insert new events and update the ones already stored (same id)."""
    if not items:
        return
    rows = [item.model_dump(mode="json", exclude=set(Event.model_computed_fields)) for item in items]
    statement = insert(events).values(rows)
    # first_seen_at is kept from the first time the event was stored, so it is never updated.
    changes = {
        c.name: statement.excluded[c.name]
        for c in events.columns
        if not c.primary_key and c.name != "first_seen_at"
    }
    connection.execute(statement.on_conflict_do_update(index_elements=[events.c.id], set_=changes))


def record_ticket_click(connection: Connection, click: TicketClick) -> None:
    connection.execute(insert(ticket_clicks).values(
        show_key=click.show_key, event_id=click.event_id, vendor=click.vendor, source=click.source, created_at=click.at,
    ))


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


def _date_matches(filters: EventFilters, now: datetime) -> list[ColumnElement[bool]]:
    """Conditions one stored date (row) must meet: upcoming, plus every filter sent except
    announced_from, which /events checks per row and /shows per show."""
    conditions: list[ColumnElement[bool]] = [events.c.starts_at >= now]
    if filters.q:
        conditions.append(_search(filters.q))
    if filters.starts_from is not None:
        conditions.append(events.c.starts_at >= filters.starts_from)
    if filters.starts_before is not None:
        conditions.append(events.c.starts_at < filters.starts_before)
    if filters.venue is not None:
        conditions.append(events.c.venue == filters.venue)
    if filters.category is not None:
        conditions.append(events.c.category == filters.category)
    return conditions


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
    query = select(events).where(*_date_matches(filters, now))
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


def list_show_dates(connection: Connection, show: str, now: datetime) -> list[ShowDate]:
    """Upcoming dates of one show (see `show_key`). The key is compared whole, so
    `colon-el-cascanueces` never picks up `colon-el-cascanueces-2`."""
    query = (
        select(events.c.id, events.c.starts_at, events.c.time_known)
        .where(_show_key == show, events.c.starts_at >= now)
        .order_by(events.c.starts_at, events.c.id)
    )
    return [ShowDate(id=row.id, starts_at=row.starts_at, time_known=row.time_known) for row in connection.execute(query)]


class VenueCount(BaseModel):
    name: str  # what to send as `venue=` to GET /events
    upcoming_events: int


def list_upcoming_venues(connection: Connection, now: datetime, category: EventCategory | None = None) -> list[VenueCount]:
    """Venues with at least one event from `now` on (of `category`, when given), by name, with how many they have."""
    conditions = [events.c.starts_at >= now]
    if category is not None:
        conditions.append(events.c.category == category)
    query = (
        select(events.c.venue, func.count())
        .where(*conditions)
        .group_by(events.c.venue)
        .order_by(events.c.venue)
    )
    return [VenueCount(name=name, upcoming_events=count) for name, count in connection.execute(query)]


def list_upcoming_shows(
    connection: Connection,
    now: datetime,
    limit: int,
    after: Position | None,
    filters: EventFilters = EventFilters(),
    sort: EventSort = "starts_at",
) -> list[Show]:
    """Shows with at least one upcoming date that matches the filters, `limit` at a time, each with
    ALL of its upcoming dates (not only the matching ones).

    By starts_at a show goes by its next date, then key. By announced it goes by its first_seen_at,
    the earliest of any of its dates (past ones included), newest first, then key descending; that
    is also what announced_from looks at, so a new date of a show we already knew is not news.
    """
    matching = select(_show_key.label("key")).where(*_date_matches(filters, now)).distinct().subquery()
    per_show = _per_show(now)
    query = select(per_show).join(matching, matching.c.key == per_show.c.key)
    if filters.announced_from is not None:
        query = query.where(per_show.c.first_seen_at >= filters.announced_from)
    if sort == "announced":
        if after is not None:
            query = query.where(tuple_(per_show.c.first_seen_at, per_show.c.key) < tuple_(*after))
        query = query.order_by(per_show.c.first_seen_at.desc(), per_show.c.key.desc())
    else:
        if after is not None:
            query = query.where(tuple_(per_show.c.next_starts_at, per_show.c.key) > tuple_(*after))
        query = query.order_by(per_show.c.next_starts_at, per_show.c.key)
    return _shows_for(connection, now, connection.execute(query.limit(limit)).all())


def get_upcoming_show(connection: Connection, key: str, now: datetime) -> Show | None:
    """One show by its key (compared whole) with all of its upcoming dates; None when it has none."""
    per_show = _per_show(now)
    query = select(per_show).where(per_show.c.key == key, per_show.c.next_starts_at.is_not(None))
    found = _shows_for(connection, now, connection.execute(query).all())
    return found[0] if found else None


def _per_show(now: datetime):
    """One row per stored show: its key, next upcoming date (null when none) and first_seen_at, the
    earliest of any of its dates, past ones included."""
    return (
        select(
            _show_key.label("key"),
            func.min(events.c.starts_at).filter(events.c.starts_at >= now).label("next_starts_at"),
            func.min(events.c.first_seen_at).label("first_seen_at"),
        )
        .group_by(_show_key)
        .subquery()
    )


def _shows_for(connection: Connection, now: datetime, page: list[Row]) -> list[Show]:
    """Builds the shows of `page` (rows with key and first_seen_at, in order) with their upcoming dates."""
    if not page:
        return []
    dates = select(events, _show_key.label("show_key")).where(
        _show_key.in_([row.key for row in page]), events.c.starts_at >= now
    ).order_by(events.c.starts_at, events.c.id)
    upcoming: dict[str, list[Event]] = {row.key: [] for row in page}
    for row in connection.execute(dates).mappings():
        fields = dict(row)
        upcoming[fields.pop("show_key")].append(Event.model_validate(fields))
    # A show whose rows vanished between the two queries is skipped rather than failing the page.
    return [Show.from_dates(row.key, upcoming[row.key], row.first_seen_at) for row in page if upcoming[row.key]]


JUST_ANNOUNCED_DAYS = 14


def known_show_keys(connection: Connection, keys: list[str]) -> set[str]:
    """Which of `keys` name a stored show (any date, past ones included), compared whole."""
    if not keys:
        return set()
    query = select(_show_key).where(_show_key.in_(keys)).distinct()
    return set(connection.execute(query).scalars())


def replace_featured(connection: Connection, keys: list[str]) -> None:
    """The featured shows become exactly `keys`, in that order. Run it inside one transaction."""
    connection.execute(delete(featured_shows))
    if keys:
        connection.execute(featured_shows.insert(), [{"show_key": k, "position": i} for i, k in enumerate(keys)])


def _with_image(shows: list[Show]) -> list[Show]:
    return [show for show in shows if show.image_url is not None]


def list_featured_shows(connection: Connection, now: datetime, limit: int, category: EventCategory | None = None) -> list[Show]:
    """Picked shows in their order, only those with an upcoming date and an image (of the next date),
    and of `category` when given."""
    per_show = _per_show(now)
    query = (
        select(per_show)
        .join(featured_shows, featured_shows.c.show_key == per_show.c.key)
        .where(per_show.c.next_starts_at.is_not(None))
        .order_by(featured_shows.c.position)
    )
    shows = _with_image(_shows_for(connection, now, connection.execute(query).all()))
    return [show for show in shows if category is None or show.category == category][:limit]


def list_just_announced_with_image(connection: Connection, now: datetime, limit: int, category: EventCategory | None = None) -> list[Show]:
    """Shows first seen in the last JUST_ANNOUNCED_DAYS days that have an image, newest first: what
    the home features when nothing is picked. Reads a few times `limit` because some have no image."""
    filters = EventFilters(announced_from=now - timedelta(days=JUST_ANNOUNCED_DAYS), category=category)
    found = list_upcoming_shows(connection, now, limit * 5, None, filters, "announced")
    return _with_image(found)[:limit]
