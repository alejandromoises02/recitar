from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Engine

from app.api.cursor import decode_cursor, encode_cursor
from app.api.listing import (
    DEFAULT_LIMIT, Category, Cursor, FromDay, Search, EventsAnnouncedFrom, EventsLimit, Sort, ToDay, Venue, build_filters, problem,
)
from app.api.problems import NotFoundError
from app.db import make_engine
from app.domain.event import Event, ShowDate, show_key
from app.events_repository import EventFilters, EventSort, Position, get_event, list_show_dates, list_upcoming

# (how many, after which position, which ones, in which order) -> upcoming events in that order
EventsSource = Callable[[int, Position | None, EventFilters, EventSort], list[Event]]

# event id -> (the event, upcoming dates of its show) or None when there is no such event
DetailSource = Callable[[str], tuple[Event, list[ShowDate]] | None]

router = APIRouter(tags=["events"])


class EventDetail(Event):
    other_dates: list[ShowDate]  # upcoming dates of the same show, without this one


class EventPage(BaseModel):
    items: list[Event]
    next_cursor: str | None  # null on the last page


@lru_cache
def engine() -> Engine:
    return make_engine(pooled=True)


def upcoming_events_source() -> EventsSource:
    """Reads the database only when called, so a rejected request never opens a connection."""

    def read(limit: int, after: Position | None, filters: EventFilters, sort: EventSort) -> list[Event]:
        with engine().connect() as connection:
            return list_upcoming(connection, datetime.now(timezone.utc), limit, after, filters, sort)

    return read


def event_detail_source() -> DetailSource:
    def read(event_id: str) -> tuple[Event, list[ShowDate]] | None:
        with engine().connect() as connection:
            found = get_event(connection, event_id)
            if found is None:
                return None
            return found, list_show_dates(connection, show_key(event_id), datetime.now(timezone.utc))

    return read


@router.get(
    "/events",
    response_model=EventPage,
    summary="Upcoming events, a page at a time",
    responses={
        400: problem("The cursor was not issued by this API"),
        422: problem("limit, q, from, to, venue, category, sort or announced_from is not valid"),
    },
)
def list_events(
    source: Annotated[EventsSource, Depends(upcoming_events_source)],
    limit: EventsLimit = DEFAULT_LIMIT,
    cursor: Cursor = None,
    q: Search = None,
    from_: FromDay = None,
    to: ToDay = None,
    venue: Venue = None,
    category: Category = None,
    sort: Sort = "starts_at",
    announced_from: EventsAnnouncedFrom = None,
) -> EventPage:
    """Events that have not started yet, by start time (then id), or by announcement with `sort=announced`. Follow `next_cursor` until it is
    null: new events stored while paging never make one repeat or go missing. Send the same filters
    with every page, including `sort`: a cursor only works with the order that issued it. For "just
    announced", ask `sort=announced` with `announced_from` set to the first day of the window. Days
    are Buenos Aires days: a show on Saturday at 22:00 there is a Saturday show, although it is stored
    as Sunday 01:00 UTC. One item per date; GET /shows lists each show once."""
    filters = build_filters(q, from_, to, venue, category, announced_from)
    after = decode_cursor(cursor, sort) if cursor else None
    rows = source(limit + 1, after, filters, sort)  # one extra row tells whether there is a next page
    items = rows[:limit]
    if len(rows) <= limit:
        return EventPage(items=items, next_cursor=None)
    last = items[-1]
    at = last.first_seen_at if sort == "announced" else last.starts_at
    return EventPage(items=items, next_cursor=encode_cursor(at, last.id, sort))


@router.get(
    "/events/{event_id}",
    response_model=EventDetail,
    summary="One event, with the other upcoming dates of the same show",
    responses={404: problem("There is no event with this id")},
)
def get_event_detail(event_id: str, source: Annotated[DetailSource, Depends(event_detail_source)]) -> EventDetail:
    """Every field of the event, including a past one, plus `other_dates`: the upcoming dates of the
    same show, so the client can offer them without searching."""
    found = source(event_id)
    if found is None:
        raise NotFoundError("Event not found", f"There is no event with id {event_id}.")
    event, dates = found
    return EventDetail(**event.model_dump(), other_dates=[d for d in dates if d.id != event.id])
