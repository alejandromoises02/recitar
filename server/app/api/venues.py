from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.events import engine
from app.events_repository import VenueCount, list_upcoming_venues

# () -> venues with upcoming events, by name
VenuesSource = Callable[[], list[VenueCount]]

router = APIRouter(tags=["venues"])


class VenueList(BaseModel):
    # Not paged: there are a few dozen venues. Wrapped in `items` so paging can be added later.
    items: list[VenueCount]


def upcoming_venues_source() -> VenuesSource:
    def read() -> list[VenueCount]:
        with engine().connect() as connection:
            return list_upcoming_venues(connection, datetime.now(timezone.utc))

    return read


@router.get("/venues", response_model=VenueList, summary="Venues with upcoming events")
def list_venues(source: Annotated[VenuesSource, Depends(upcoming_venues_source)]) -> VenueList:
    """Every venue with at least one upcoming event, by name, with how many it has. Send a `name`
    as `venue` to GET /events to see that venue's events."""
    return VenueList(items=source())
