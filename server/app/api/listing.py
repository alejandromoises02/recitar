"""Query parameters shared by the paged listings (GET /events and GET /shows), so both accept the
same names, limits and validation, and both document them the same way."""

from datetime import date
from typing import Annotated

from fastapi import Query
from pydantic import StringConstraints

from app.api.problems import MEDIA_TYPE, InvalidParameterError, Problem
from app.domain.event import EventCategory
from app.domain.local_time import day_window, start_of_day
from app.events_repository import EventFilters, EventSort

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_QUERY_LENGTH = 100
MAX_VENUES = 20

EventsLimit = Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Events per page")]
ShowsLimit = Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Shows per page")]
Cursor = Annotated[str | None, Query(description="next_cursor of the previous page; leave out for the first")]
Search = Annotated[
    str | None,
    Query(
        max_length=MAX_QUERY_LENGTH,
        description="Search the title, artist and venue: every word must appear, ignoring case and accents",
    ),
]
FromDay = Annotated[date | None, Query(alias="from", description="First day, YYYY-MM-DD, in Buenos Aires time (included)")]
ToDay = Annotated[date | None, Query(description="Last day, YYYY-MM-DD, in Buenos Aires time (included)")]
Venue = Annotated[
    list[Annotated[str, StringConstraints(max_length=MAX_QUERY_LENGTH)]] | None,
    Query(
        max_length=MAX_VENUES,
        description=f"Only these venues: each a `name` from GET /venues, exactly. Repeat it (up to {MAX_VENUES}) "
        "to list the events of any of them",
    ),
]
Category = Annotated[EventCategory | None, Query(description="Only this kind of event")]
Sort = Annotated[
    EventSort,
    Query(description="`starts_at`: soonest first. `announced`: most recently announced (`first_seen_at`) first"),
]
EventsAnnouncedFrom = Annotated[
    date | None,
    Query(description="Only events first seen on or after this day, YYYY-MM-DD, in Buenos Aires time"),
]
ShowsAnnouncedFrom = Annotated[
    date | None,
    Query(
        description="Only shows first seen (any of their dates, past ones included) on or after this day, "
        "YYYY-MM-DD, in Buenos Aires time"
    ),
]


def _blank_is_none(value: str | None) -> str | None:
    return value.strip() or None if value else None


def _venues(given: list[str] | None) -> tuple[str, ...]:
    """Each venue once, in the order given; blanks are left out."""
    return tuple(dict.fromkeys(name for name in (_blank_is_none(v) for v in given or []) if name))


def build_filters(
    q: str | None, from_: date | None, to: date | None, venue: list[str] | None, category: EventCategory | None,
    announced_from: date | None,
) -> EventFilters:
    if from_ and to and to < from_:
        raise InvalidParameterError(f"`to` ({to}) is before `from` ({from_}).")
    starts_from, starts_before = day_window(from_, to)
    return EventFilters(
        q=_blank_is_none(q), starts_from=starts_from, starts_before=starts_before,
        venues=_venues(venue), category=category,
        announced_from=start_of_day(announced_from) if announced_from else None,
    )


def problem(description: str) -> dict:
    return {"description": description, "content": {MEDIA_TYPE: {"schema": Problem.model_json_schema()}}}
