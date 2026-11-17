from datetime import datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, computed_field, field_serializer, model_validator

from app.domain.local_time import BUENOS_AIRES
from app.domain.titles import tidy_title

# What a show is stored at while its venue is not confirmed yet (see scrapers.venues).
VENUE_TO_BE_CONFIRMED = "Lugar a confirmar"

EventCategory = Literal["concert", "tribute", "theatre", "party", "other"]

# Where an image comes from. Only "source" is unlicensed: it is the image the ticket seller
# publishes, shown straight from there. Before a public launch every "source" image must be
# replaced by a "licensed" (free licence, copied with credit) or "venue" one, or by no image.
ImageOrigin = Literal["source", "licensed", "venue"]


class TicketLink(BaseModel):
    vendor: str
    url: str


class Event(BaseModel):
    """Public facts about one show. The client's types are generated from the API schema
    (client/src/api/schema.ts) and mapped to its own Event in client/src/features/events/."""

    # Fields with a default are always sent (as null), so the schema lists them as required.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    id: str
    category: EventCategory
    title: str  # as published by the source, verbatim
    artist: str | None = None  # from the source, else read from the title (pipeline.add_artists); may stay empty
    venue: str
    city: str | None = None
    region: str | None = None  # ISO 3166-2 subdivision, e.g. "AR-C" (Ciudad de Buenos Aires)
    country: str | None = None  # ISO 3166-1 alpha-2, e.g. "AR"
    starts_at: AwareDatetime
    time_known: bool = True  # False when the source gave only the day: starts_at is then that day's midnight
    ticket_links: list[TicketLink]
    source_url: str
    image_url: str | None = None
    image_origin: ImageOrigin | None = None
    image_author: str | None = None  # credit, required by most free licences
    image_license: str | None = None  # e.g. "CC BY-SA 4.0"
    image_source_url: str | None = None  # page where the image and its licence are published
    updated_at: AwareDatetime  # last time a scraper read it
    # First time a scraper read it: when we learned the show was announced. Stored once and never
    # overwritten (see upsert_events). A freshly scraped event leaves it out and takes updated_at.
    first_seen_at: AwareDatetime

    @model_validator(mode="before")
    @classmethod
    def _first_seen_defaults_to_now_seen(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("first_seen_at") is None and "updated_at" in data:
            return {**data, "first_seen_at": data["updated_at"]}
        return data

    @computed_field
    @property
    def name(self) -> str:
        """The title made readable (see domain/titles.py): what the client shows. Computed on every
        read, not stored, so a better rule applies at once without scraping again."""
        return tidy_title(self.title, self.id.split("-", 1)[0]).name

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

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    id: str
    starts_at: AwareDatetime
    time_known: bool = True

    @field_serializer("starts_at")
    def _in_buenos_aires_time(self, value: datetime) -> datetime:
        return value.astimezone(BUENOS_AIRES)


class ShowDateTickets(ShowDate):
    """One upcoming date of a show in a listing, with where to buy it."""

    ticket_links: list[TicketLink]


class Show(BaseModel):
    """A show once, with all of its upcoming dates. Display fields come from its next date."""

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    id: str  # the show key: an event id without its date (see show_key)
    category: EventCategory
    title: str
    name: str  # readable title, as Event.name
    artist: str | None = None
    venue: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    source_url: str
    image_url: str | None = None
    image_origin: ImageOrigin | None = None
    image_author: str | None = None
    image_license: str | None = None
    image_source_url: str | None = None
    first_seen_at: AwareDatetime  # the earliest first_seen_at of any of its dates, past ones included
    updated_at: AwareDatetime  # the last time a scraper read any of its upcoming dates ("updated X ago")
    dates: list[ShowDateTickets]  # upcoming only, soonest first; never empty

    @model_validator(mode="after")
    def _has_dates_and_matching_image(self) -> "Show":
        if not self.dates:
            raise ValueError("a show has at least one upcoming date")
        if (self.image_url is None) != (self.image_origin is None):
            raise ValueError("image_url and image_origin must be given together")
        return self

    @classmethod
    def from_dates(cls, show_id: str, upcoming: list[Event], first_seen_at: datetime) -> "Show":
        """`upcoming`: the show's upcoming events, soonest first."""
        display = upcoming[0].model_dump(include=set(cls.model_fields) - {"id", "first_seen_at", "updated_at", "dates"})
        dates = [ShowDateTickets(id=e.id, starts_at=e.starts_at, time_known=e.time_known, ticket_links=e.ticket_links) for e in upcoming]
        updated_at = max(e.updated_at for e in upcoming)
        return cls(id=show_id, first_seen_at=first_seen_at, updated_at=updated_at, dates=dates, **display)
