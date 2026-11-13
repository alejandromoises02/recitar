"""Featured shows for the home: picked by hand with PUT /featured (admin only), read by anyone."""

from datetime import datetime, timezone
from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.admin_auth import require_admin
from app.api.events import engine
from app.api.listing import problem
from app.api.problems import InvalidParameterError
from app.domain.event import Show
from app.events_repository import (
    known_show_keys, list_featured_shows, list_just_announced_with_image, replace_featured,
)

FEATURED_LIMIT = 10  # what the home's record fan can show
MAX_FEATURED = 20

router = APIRouter(tags=["featured"])


class FeaturedStore(Protocol):
    def known_show_ids(self, ids: list[str]) -> set[str]: ...
    def replace(self, ids: list[str]) -> None: ...
    def picked(self, limit: int) -> list[Show]: ...
    def just_announced(self, limit: int) -> list[Show]: ...


class _DatabaseStore:
    """Opens a connection per call, so a rejected request never touches the database."""

    def known_show_ids(self, ids: list[str]) -> set[str]:
        with engine().connect() as connection:
            return known_show_keys(connection, ids)

    def replace(self, ids: list[str]) -> None:
        with engine().begin() as connection:  # one transaction: the old list or the new one, never half
            replace_featured(connection, ids)

    def picked(self, limit: int) -> list[Show]:
        with engine().connect() as connection:
            return list_featured_shows(connection, datetime.now(timezone.utc), limit)

    def just_announced(self, limit: int) -> list[Show]:
        with engine().connect() as connection:
            return list_just_announced_with_image(connection, datetime.now(timezone.utc), limit)


def featured_store() -> FeaturedStore:
    return _DatabaseStore()


class FeaturedIds(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a misspelled field is an error, not silently ignored

    show_ids: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(
        max_length=MAX_FEATURED,
        description="Show ids (as GET /shows gives them) in the order the home shows them. [] clears the list.",
    )

    @field_validator("show_ids", mode="before")
    @classmethod
    def _trimmed(cls, ids: object) -> object:
        """Trimmed before the length checks, so a blank id is invalid rather than unknown."""
        return [i.strip() if isinstance(i, str) else i for i in ids] if isinstance(ids, list) else ids

    @field_validator("show_ids")
    @classmethod
    def _unique(cls, ids: list[str]) -> list[str]:
        if len(set(ids)) != len(ids):
            raise ValueError("each show id may appear only once")
        return ids


class Featured(BaseModel):
    kind: Literal["picked", "just_announced"]  # just_announced when nothing picked is showable
    items: list[Show]


@router.get("/featured", response_model=Featured, summary="The shows the home features")
def get_featured(store: Annotated[FeaturedStore, Depends(featured_store)]) -> Featured:
    """Up to 10 shows, each with all its upcoming dates (as in GET /shows) and an image. The ones
    picked by hand, in their order; when none of them can be shown (none picked, all past, or
    without an image), the shows first seen in the last 14 days that have an image, newest first."""
    picked = store.picked(FEATURED_LIMIT)
    if picked:
        return Featured(kind="picked", items=picked[:FEATURED_LIMIT])
    return Featured(kind="just_announced", items=store.just_announced(FEATURED_LIMIT)[:FEATURED_LIMIT])


@router.put(
    "/featured",
    response_model=FeaturedIds,
    summary="Pick the featured shows (admin only)",
    dependencies=[Depends(require_admin)],
    responses={
        401: problem("No admin token, or not the right one"),
        422: problem("Unknown or repeated show ids, or more than 20"),
        503: problem("This server has no admin token configured"),
    },
)
def put_featured(body: FeaturedIds, store: Annotated[FeaturedStore, Depends(featured_store)]) -> FeaturedIds:
    """Replaces the whole list. Every id must be a stored show; nothing is written otherwise."""
    unknown = sorted(set(body.show_ids) - store.known_show_ids(body.show_ids))
    if unknown:
        raise InvalidParameterError(f"Unknown show ids: {', '.join(unknown)}.")
    store.replace(body.show_ids)
    return body
