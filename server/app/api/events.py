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
from app.events_repository import list_upcoming

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# (how many, after which (starts_at, id)) -> upcoming events in order
EventsSource = Callable[[int, tuple[datetime, str] | None], list[Event]]

router = APIRouter(tags=["events"])


class EventPage(BaseModel):
    items: list[Event]
    next_cursor: str | None  # null on the last page


@lru_cache
def _engine() -> Engine:
    return make_engine(pooled=True)


def upcoming_events_source() -> EventsSource:
    """Reads the database only when called, so a rejected request never opens a connection."""

    def read(limit: int, after: tuple[datetime, str] | None) -> list[Event]:
        with _engine().connect() as connection:
            return list_upcoming(connection, datetime.now(timezone.utc), limit, after)

    return read


def _problem(description: str) -> dict:
    return {"description": description, "content": {MEDIA_TYPE: {"schema": Problem.model_json_schema()}}}


@router.get(
    "/events",
    response_model=EventPage,
    summary="Upcoming events, a page at a time",
    responses={400: _problem("The cursor was not issued by this API"), 422: _problem("limit is out of range")},
)
def list_events(
    source: Annotated[EventsSource, Depends(upcoming_events_source)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Events per page")] = DEFAULT_LIMIT,
    cursor: Annotated[str | None, Query(description="next_cursor of the previous page; leave out for the first")] = None,
) -> EventPage:
    """Events that have not started yet, by start time (then id). Follow `next_cursor` until it is
    null: new events stored while paging never make one repeat or go missing."""
    after = decode_cursor(cursor) if cursor else None
    rows = source(limit + 1, after)  # one extra row tells whether there is a next page
    items = rows[:limit]
    return EventPage(items=items, next_cursor=encode_cursor(items[-1]) if len(rows) > limit else None)
