"""Opaque page cursors: the (starts_at, id) of the last event of a page, as URL-safe base64 JSON.

Clients must treat the value as opaque; only this module reads or writes it.
"""

import base64
import binascii
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError

from app.domain.event import Event


class InvalidCursorError(ValueError):
    pass


class _Position(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: AwareDatetime
    id: str


def encode_cursor(last: Event) -> str:
    raw = _Position(starts_at=last.starts_at, id=last.id).model_dump_json().encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
    except binascii.Error as error:
        raise InvalidCursorError(cursor) from error
    try:
        position = _Position.model_validate_json(raw)
    except ValidationError as error:  # not JSON, or not a position we issued
        raise InvalidCursorError(cursor) from error
    return position.starts_at, position.id
