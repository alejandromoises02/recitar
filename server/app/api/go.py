import logging
from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse

from app.api.events import engine
from app.api.listing import problem
from app.api.problems import NotFoundError
from app.domain.event import Event, show_key
from app.domain.ticket_redirect import TicketClick, destination, looks_like_bot, source_of, with_utm_source
from app.events_repository import get_event, record_ticket_click

# event id -> the event, or None when there is no such event
EventLookup = Callable[[str], Event | None]
# stores one click
ClickRecorder = Callable[[TicketClick], None]

router = APIRouter(tags=["tickets"])
log = logging.getLogger(__name__)


def go_event_source() -> EventLookup:
    def read(event_id: str) -> Event | None:
        with engine().connect() as connection:
            return get_event(connection, event_id)

    return read


def click_recorder() -> ClickRecorder:
    def write(click: TicketClick) -> None:
        with engine().begin() as connection:
            record_ticket_click(connection, click)

    return write


@router.get(
    "/go/{event_id}",
    status_code=302,
    response_class=RedirectResponse,
    summary="Count a ticket click and send the visitor to the ticket page",
    responses={
        302: {"description": "To a ticket link stored for this date (or the show's page at its source), with utm_source=recitar"},
        404: problem("There is no date with this id, or it has no web link to go to"),
    },
)
def go(
    event_id: str,
    request: Request,
    lookup: Annotated[EventLookup, Depends(go_event_source)],
    record: Annotated[ClickRecorder, Depends(click_recorder)],
    v: Annotated[str | None, Query(description="The ticketer, a `vendor` of the date's ticket links; the first link when left out or unknown")] = None,
    from_: Annotated[str | None, Query(alias="from", description='Where in the app the click came from: "show" or "spotlight"; anything else is counted as "other"')] = None,
) -> RedirectResponse:
    """Every ticket button goes through here. The destination is always a link the scrapers stored for
    this date, never something the request carries, so this cannot redirect to a site of someone's choosing.

    The click is counted (show, date, ticketer, place in the app, time; nothing about the person), except
    when the caller looks like a crawler or a link preview. Counting never gets in the way: if it fails, the
    visitor is still sent on. Parameters that are wrong are ignored rather than refused, for the same reason."""
    event = lookup(event_id)
    where = None if event is None else destination(event, v)
    if event is None or where is None:
        raise NotFoundError("Ticket link not found", f"There is no date with id {event_id} to buy tickets for.")
    if not looks_like_bot(request.headers.get("user-agent")):
        click = TicketClick(show_key(event.id), event.id, where.vendor, source_of(from_), datetime.now(timezone.utc))
        try:
            record(click)
        except Exception:  # noqa: BLE001 - whatever goes wrong while counting, the visitor still gets to the tickets
            log.exception("Could not store a ticket click for %s", event.id)
    return RedirectResponse(with_utm_source(where.url), status_code=302, headers={"Cache-Control": "no-store"})
