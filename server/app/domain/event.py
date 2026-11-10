from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, field_serializer, model_validator

from app.domain.local_time import BUENOS_AIRES

EventCategory = Literal["concert", "theatre", "party", "other"]

# Where an image comes from. Only "source" is unlicensed: it is the image the ticket seller
# publishes, shown straight from there. Before a public launch every "source" image must be
# replaced by a "licensed" (free licence, copied with credit) or "venue" one, or by no image.
ImageOrigin = Literal["source", "licensed", "venue"]


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
    image_url: str | None = None
    image_origin: ImageOrigin | None = None
    image_author: str | None = None  # credit, required by most free licences
    image_license: str | None = None  # e.g. "CC BY-SA 4.0"
    image_source_url: str | None = None  # page where the image and its licence are published
    updated_at: AwareDatetime

    @field_serializer("starts_at")
    def _in_buenos_aires_time(self, value: datetime) -> datetime:
        """Written with the Buenos Aires offset (e.g. 22:00-03:00, not 01:00Z next day), so a client
        reads the local day and hour as they come. Same instant either way."""
        return value.astimezone(BUENOS_AIRES)

    @model_validator(mode="after")
    def _origin_goes_with_the_image(self) -> "Event":
        if (self.image_url is None) != (self.image_origin is None):
            raise ValueError("image_url and image_origin must be given together")
        return self


def show_key(event_id: str) -> str:
    """Event ids are `<source>-<show>-<YYYYMMDDTHHMM>`; without the date they name the show, so
    every date of one show shares it."""
    return event_id.rsplit("-", 1)[0]


class ShowDate(BaseModel):
    """Another date of the same show: enough to link to it."""

    id: str
    starts_at: AwareDatetime

    @field_serializer("starts_at")
    def _in_buenos_aires_time(self, value: datetime) -> datetime:
        return value.astimezone(BUENOS_AIRES)
