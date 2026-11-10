from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Engine

from app.api.cursor import decode_cursor, encode_cursor
from app.api.problems import MEDIA_TYPE, Problem
from app.db import make_engine
from app.domain.event import Event
from app.events_repository import EventFilters, list_upcoming

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

MAX_QUERY_LENGTH = 100

# (how many, after which (starts_at, id), which ones) -> upcoming events in order
EventsSource = Callable[[int, tuple[datetime, str] | None, EventFilters], list[Event]]

router = APIRouter(tags=["events"])


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


def _problem(description: str) -> dict:
    return {"description": description, "content": {MEDIA_TYPE: {"schema": Problem.model_json_schema()}}}


@router.get(
    "/events",
    response_model=EventPage,
    summary="Upcoming events, a page at a time",
    responses={400: _problem("The cursor was not issued by this API"), 422: _problem("limit or q is out of range")},
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
) -> EventPage:
    """Events that have not started yet, by start time (then id). Follow `next_cursor` until it is
    null: new events stored while paging never make one repeat or go missing. Send the same filters
    with every page."""
    after = decode_cursor(cursor) if cursor else None
    filters = EventFilters(q=q.strip() or None if q else None)
    rows = source(limit + 1, after, filters)  # one extra row tells whether there is a next page
    items = rows[:limit]
    return EventPage(items=items, next_cursor=encode_cursor(items[-1]) if len(rows) > limit else None)
