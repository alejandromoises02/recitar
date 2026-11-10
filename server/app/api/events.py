from datetime import date, datetime, timezone
from functools import lru_cache
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Engine

from app.api.cursor import decode_cursor, encode_cursor
from app.api.problems import MEDIA_TYPE, InvalidParameterError, NotFoundError, Problem
from app.db import make_engine
from app.domain.event import Event, ShowDate, show_key
from app.domain.local_time import day_window
from app.events_repository import EventFilters, get_event, list_show_dates, list_upcoming

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

MAX_QUERY_LENGTH = 100

# (how many, after which (starts_at, id), which ones) -> upcoming events in order
EventsSource = Callable[[int, tuple[datetime, str] | None, EventFilters], list[Event]]

# event id -> (the event, upcoming dates of its show) or None when there is no such event
DetailSource = Callable[[str], tuple[Event, list[ShowDate]] | None]

router = APIRouter(tags=["events"])


class EventDetail(Event):
    other_dates: list[ShowDate]  # upcoming dates of the same show, without this one


class EventPage(BaseModel):
    items: list[Event]
    next_cursor: str | None  # null on the last page


@lru_cache
def _engine() -> Engine:
    return make_engine(pooled=True)


def upcoming_events_source() -> EventsSource:
    """Reads the database only when called, so a rejected request never opens a connection."""

    def read(limit: int, after: tuple[datetime, str] | None, filters: EventFilters) -> list[Event]:
        with _engine().connect() as connection:
            return list_upcoming(connection, datetime.now(timezone.utc), limit, after, filters)

    return read


def event_detail_source() -> DetailSource:
    def read(event_id: str) -> tuple[Event, list[ShowDate]] | None:
        with _engine().connect() as connection:
            found = get_event(connection, event_id)
            if found is None:
                return None
            return found, list_show_dates(connection, show_key(event_id), datetime.now(timezone.utc))

    return read


def _problem(description: str) -> dict:
    return {"description": description, "content": {MEDIA_TYPE: {"schema": Problem.model_json_schema()}}}


@router.get(
    "/events",
    response_model=EventPage,
    summary="Upcoming events, a page at a time",
    responses={400: _problem("The cursor was not issued by this API"), 422: _problem("limit, q, from or to is not valid")},
)
def list_events(
    source: Annotated[EventsSource, Depends(upcoming_events_source)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Events per page")] = DEFAULT_LIMIT,
    cursor: Annotated[str | None, Query(description="next_cursor of the previous page; leave out for the first")] = None,
    q: Annotated[
        str | None,
        Query(
            max_length=MAX_QUERY_LENGTH,
            description="Search the title, artist and venue: every word must appear, ignoring case and accents",
        ),
    ] = None,
    from_: Annotated[
        date | None, Query(alias="from", description="First day, YYYY-MM-DD, in Buenos Aires time (included)")
    ] = None,
    to: Annotated[date | None, Query(description="Last day, YYYY-MM-DD, in Buenos Aires time (included)")] = None,
) -> EventPage:
    """Events that have not started yet, by start time (then id). Follow `next_cursor` until it is
    null: new events stored while paging never make one repeat or go missing. Send the same filters
    with every page. Days are Buenos Aires days: a show on Saturday at 22:00 there is a Saturday
    show, although it is stored as Sunday 01:00 UTC."""
    if from_ and to and to < from_:
        raise InvalidParameterError(f"`to` ({to}) is before `from` ({from_}).")
    after = decode_cursor(cursor) if cursor else None
    starts_from, starts_before = day_window(from_, to)
    filters = EventFilters(q=q.strip() or None if q else None, starts_from=starts_from, starts_before=starts_before)
    rows = source(limit + 1, after, filters)  # one extra row tells whether there is a next page
    items = rows[:limit]
    return EventPage(items=items, next_cursor=encode_cursor(items[-1]) if len(rows) > limit else None)


@router.get(
    "/events/{event_id}",
    response_model=EventDetail,
    summary="One event, with the other upcoming dates of the same show",
    responses={404: _problem("There is no event with this id")},
)
def get_event_detail(event_id: str, source: Annotated[DetailSource, Depends(event_detail_source)]) -> EventDetail:
    """Every field of the event, including a past one, plus `other_dates`: the upcoming dates of the
    same show, so the client can offer them without searching."""
    found = source(event_id)
    if found is None:
        raise NotFoundError("Event not found", f"There is no event with id {event_id}.")
    event, dates = found
    return EventDetail(**event.model_dump(), other_dates=[d for d in dates if d.id != event.id])
