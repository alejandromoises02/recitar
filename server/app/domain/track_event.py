from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

EventName = Literal[
    "visit started", "show opened", "filter used", "no results", "show shared", "more at venue clicked"
]
# the events that are about one show
SHOW_EVENTS = ("show opened", "show shared", "more at venue clicked")
FilterName = Literal["search", "venue", "when", "day", "group"]


class TrackEvent(BaseModel):
    """One thing the app tells us happened: a visit began, a show was opened, a filter was used.

    Nothing about the person: the session id is a random value the app makes when it starts and keeps only
    in memory. Everything is bounded because anyone can call the endpoint."""

    model_config = ConfigDict(extra="forbid")

    event: EventName
    session_id: str = Field(pattern=r"^[A-Za-z0-9-]{8,64}$")
    show_key: str | None = Field(default=None, pattern=r"^[a-z0-9-]{1,200}$")
    show_name: str | None = Field(default=None, max_length=120)
    venue: str | None = Field(default=None, max_length=120)
    filter: FilterName | None = None
    filters: list[FilterName] | None = Field(default=None, max_length=5)  # which filters were on when nothing was found
    when: str | None = Field(default=None, pattern=r"^[a-z0-9-]{1,20}$")  # the date range or day asked for
    value: str | None = Field(default=None, max_length=60)

    @model_validator(mode="after")
    def _complete(self) -> Self:
        if self.event in SHOW_EVENTS and self.show_key is None:
            raise ValueError(f"{self.event} needs show_key")
        if self.event == "no results" and not self.filters:
            raise ValueError("an empty result needs the filters that were on")
        if self.event == "filter used" and self.filter is None:
            raise ValueError("a filter event needs filter")
        if self.filter == "search":
            self.value = None  # what people type could be anything about them: only that search was used is kept
        return self
