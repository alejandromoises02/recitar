import logging
from typing import Annotated, Callable

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

from app.analytics import forward_track
from app.api.rate_limit import limit_track
from app.domain.device import device_of
from app.domain.ticket_redirect import looks_like_bot
from app.domain.track_event import TrackEvent

# sends one event and the device class it came from to the analytics tool
TrackForwarder = Callable[[TrackEvent, str], None]

router = APIRouter(tags=["analytics"])
log = logging.getLogger(__name__)


def track_forwarder() -> TrackForwarder:
    return forward_track


def _forward_safely(forward: TrackForwarder, event: TrackEvent, device: str) -> None:
    try:
        forward(event, device)
    except Exception:  # noqa: BLE001 - analytics never gets in the way, whatever goes wrong
        log.exception("Could not forward a %s event", event.event)


@router.post(
    "/track",
    status_code=204,
    summary="Tell us a visit began, a show was opened or a filter was used",
    dependencies=[Depends(limit_track)],
    responses={
        413: {"description": "The body is over 4096 bytes"},
        422: {"description": "The event is not one we know, or it is incomplete or too long"},
        429: {"description": "Too many events from this caller this minute; Retry-After says when to send again"},
    },
)
def track(
    event: TrackEvent,
    request: Request,
    background: BackgroundTasks,
    forward: Annotated[TrackForwarder, Depends(track_forwarder)],
) -> Response:
    """The app reports what visitors do, so the owner can see it in the analytics tool. Nothing is stored here
    and nothing about the person travels: the session id is random and lives only while the app is open.
    Only a coarse device class (ios, android, desktop) is derived from the browser and sent; its text is not. Crawlers are answered and ignored. The answer never depends on the analytics tool."""
    user_agent = request.headers.get("user-agent")
    if not looks_like_bot(user_agent):
        background.add_task(_forward_safely, forward, event, device_of(user_agent))
    return Response(status_code=204)
