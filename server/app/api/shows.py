from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.cursor import decode_cursor, encode_cursor
from app.api.events import engine
from app.api.listing import (
    DEFAULT_LIMIT, Category, Cursor, FromDay, Search, ShowsAnnouncedFrom, ShowsLimit, Sort, ToDay, Venue, build_filters, problem,
)
from app.domain.event import Show
from app.events_repository import EventFilters, EventSort, Position, list_upcoming_shows

# (how many, after which position, which ones, in which order) -> upcoming shows in that order
ShowsSource = Callable[[int, Position | None, EventFilters, EventSort], list[Show]]

router = APIRouter(tags=["shows"])


class ShowPage(BaseModel):
    items: list[Show]
    next_cursor: str | None  # null on the last page


def upcoming_shows_source() -> ShowsSource:
    """Reads the database only when called, so a rejected request never opens a connection."""

    def read(limit: int, after: Position | None, filters: EventFilters, sort: EventSort) -> list[Show]:
        with engine().connect() as connection:
            return list_upcoming_shows(connection, datetime.now(timezone.utc), limit, after, filters, sort)

    return read


@router.get(
    "/shows",
    response_model=ShowPage,
    summary="Upcoming shows, each once with all of its dates, a page at a time",
    responses={
        400: problem("The cursor was not issued by this API"),
        422: problem("limit, q, from, to, venue, category, sort or announced_from is not valid"),
    },
)
def list_shows(
    source: Annotated[ShowsSource, Depends(upcoming_shows_source)],
    limit: ShowsLimit = DEFAULT_LIMIT,
    cursor: Cursor = None,
    q: Search = None,
    from_: FromDay = None,
    to: ToDay = None,
    venue: Venue = None,
    category: Category = None,
    sort: Sort = "starts_at",
    announced_from: ShowsAnnouncedFrom = None,
) -> ShowPage:
    """Each show once (the dates of one show share its `id`, an event id without the date), with all
    of its upcoming dates in `dates`, soonest first, each with its own event id and ticket links.

    The filters are the ones of GET /events and apply to the dates: a show is listed when any of its
    upcoming dates matches, and it still brings all of them. `announced_from` and `sort=announced`
    look at the show's `first_seen_at`, the first time any of its dates was seen, so a new date of a
    show we already knew does not make it news. By default shows go by their next date (then id).
    Paging works as in GET /events: follow `next_cursor`, send the same parameters with every page."""
    filters = build_filters(q, from_, to, venue, category, announced_from)
    after = decode_cursor(cursor, sort) if cursor else None
    rows = source(limit + 1, after, filters, sort)  # one extra row tells whether there is a next page
    items = rows[:limit]
    if len(rows) <= limit:
        return ShowPage(items=items, next_cursor=None)
    last = items[-1]
    at = last.first_seen_at if sort == "announced" else last.dates[0].starts_at
    return ShowPage(items=items, next_cursor=encode_cursor(at, last.id, sort))
