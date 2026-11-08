from typing import Literal

from pydantic import AwareDatetime, BaseModel

EventCategory = Literal["concert", "theatre", "other"]


class TicketLink(BaseModel):
    vendor: str
    url: str


class Event(BaseModel):
    """Public facts about one show. Mirrors client/src/features/events/domain/event.ts."""

    id: str
    category: EventCategory
    artist: str
    venue: str
    starts_at: AwareDatetime
    ticket_links: list[TicketLink]
    source_url: str
    updated_at: AwareDatetime
