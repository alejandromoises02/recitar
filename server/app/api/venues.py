from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.events import engine
from app.api.listing import Category, problem
from app.domain.event import EventCategory
from app.events_repository import VenueCount, list_upcoming_venues

# category or None -> venues with upcoming events (of that kind), by name
VenuesSource = Callable[[EventCategory | None], list[VenueCount]]

router = APIRouter(tags=["venues"])


class VenueList(BaseModel):
    # Not paged: there are a few dozen venues. Wrapped in `items` so paging can be added later.
    items: list[VenueCount]


def upcoming_venues_source() -> VenuesSource:
    def read(category: EventCategory | None = None) -> list[VenueCount]:
        with engine().connect() as connection:
            return list_upcoming_venues(connection, datetime.now(timezone.utc), category)

    return read


@router.get(
    "/venues", response_model=VenueList, summary="Venues with upcoming events",
    responses={422: problem("category is not a known kind of event")},
)
def list_venues(source: Annotated[VenuesSource, Depends(upcoming_venues_source)], category: Category = None) -> VenueList:
    """Every venue with at least one upcoming event, by name, with how many it has. With `category`,
    only events of that kind are counted, and venues with none are left out. Send a `name` as `venue`
    to GET /events to see that venue's events."""
    return VenueList(items=source(category))
