from typing import Literal

from pydantic import AwareDatetime, BaseModel

EventCategory = Literal["concert", "theatre", "party", "other"]


class TicketLink(BaseModel):
    vendor: str
    url: str


class Event(BaseModel):
    """Public facts about one show. Mirrors client/src/features/events/domain/event.ts."""

    id: str
    category: EventCategory
    title: str  # as published by the source, verbatim
    artist: str | None = None  # extracted from the title later; empty until then
    venue: str
    city: str | None = None
    region: str | None = None  # ISO 3166-2 subdivision, e.g. "AR-C" (Ciudad de Buenos Aires)
    country: str | None = None  # ISO 3166-1 alpha-2, e.g. "AR"
    starts_at: AwareDatetime
    ticket_links: list[TicketLink]
    source_url: str
    updated_at: AwareDatetime
