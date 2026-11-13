"""Opaque page cursors: the position of the last item (event or show) of a page, as URL-safe base64 JSON.

The position is (starts_at, id) when listing by date and (first_seen_at, id) when listing by
announcement. Each cursor carries only the key of its own order, so a cursor issued for one order
is rejected by the other instead of skipping events. Clients must treat the value as opaque; only
this module reads or writes it.
"""

import base64
import binascii
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError

from app.events_repository import EventSort, Position


class InvalidCursorError(ValueError):
    pass


class _Position(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: AwareDatetime | None = None
    first_seen_at: AwareDatetime | None = None
    id: str


def _key(sort: EventSort) -> str:
    return "first_seen_at" if sort == "announced" else "starts_at"


def encode_cursor(at: datetime, id_: str, sort: EventSort = "starts_at") -> str:
    """`at` is the sort key of the last item: its starts_at (for a show, its next date) or its
    first_seen_at."""
    key = _key(sort)
    position = _Position.model_validate({key: at, "id": id_})
    raw = position.model_dump_json(include={key, "id"}).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str, sort: EventSort = "starts_at") -> Position:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
    except binascii.Error as error:
        raise InvalidCursorError(cursor) from error
    try:
        position = _Position.model_validate_json(raw)
    except ValidationError as error:  # not JSON, or not a position we issued
        raise InvalidCursorError(cursor) from error
    at = getattr(position, _key(sort))
    if at is None or position.model_fields_set != {_key(sort), "id"}:  # issued for the other order
        raise InvalidCursorError(cursor)
    return at, position.id
