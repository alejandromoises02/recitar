"""Product analytics sent to PostHog from the server, so the numbers do not depend on ad blockers.

Off unless POSTHOG_API_KEY is set (the project's public token, in server/.env). POSTHOG_HOST picks the
region: https://us.i.posthog.com (default), https://eu.i.posthog.com or a self-hosted address. Events are
anonymous on purpose: a random id per event, no person profile, no IP, no user agent.

PostHog answers `200 {"status":"Ok"}` to any key, valid or not (checked 2026-11-15), so a 200 proves nothing:
look for the events in the PostHog dashboard to know the key works.
"""

import logging
import os
import uuid
from typing import Callable

import httpx

from app.domain.ticket_redirect import TicketClick
from app.domain.track_event import TrackEvent

DEFAULT_HOST = "https://us.i.posthog.com"
CAPTURE_PATH = "/i/v0/e/"
TIMEOUT_SECONDS = 3.0
TICKET_CLICK_EVENT = "ticket link clicked"

log = logging.getLogger(__name__)

# (url, json, timeout) -> the answer; httpx.post in production, a fake in tests
Post = Callable[..., httpx.Response]


def posthog_config() -> tuple[str, str] | None:
    """(project key, host) from the environment, or None when analytics is off."""
    key = (os.environ.get("POSTHOG_API_KEY") or "").strip()
    if not key:
        return None
    host = (os.environ.get("POSTHOG_HOST") or DEFAULT_HOST).strip().rstrip("/")
    return key, host


ENVIRONMENTS = ("dev", "test", "prod")


def environment_name() -> str:
    """Which stage this server is: APP_ENV, one of dev / test / prod (dev when unset), else "unknown".
    Sent on every event so one PostHog dashboard can be filtered per stage."""
    value = (os.environ.get("APP_ENV") or "dev").strip().lower()
    return value if value in ENVIRONMENTS else "unknown"


def ticket_click_payload(api_key: str, click: TicketClick, environment: str) -> dict:
    """The click as a PostHog event: what the count stores and nothing about the person."""
    return {
        "api_key": api_key,
        "event": TICKET_CLICK_EVENT,
        "distinct_id": str(uuid.uuid4()),  # one id per event: two clicks are never linked to one visitor
        "properties": {
            "show_key": click.show_key,
            "show_name": click.show_name,
            "venue": click.venue,
            "device": click.device,
            "environment": environment,
            "event_id": click.event_id,
            "vendor": click.vendor,
            "source": click.source,
            "$process_person_profile": False,
            "$geoip_disable": True,  # the request comes from our server, so its location means nothing
        },
        "timestamp": click.at.isoformat(),
    }


def forward_ticket_click(click: TicketClick, post: Post = httpx.post) -> None:
    """Sends the click to PostHog. Never raises over the network: analytics must not get in anyone's way."""
    config = posthog_config()
    if config is None:
        return
    api_key, host = config
    try:
        post(f"{host}{CAPTURE_PATH}", json=ticket_click_payload(api_key, click, environment_name()), timeout=TIMEOUT_SECONDS).raise_for_status()
    except httpx.HTTPStatusError as error:
        log.warning("PostHog refused a ticket click event: HTTP %s", error.response.status_code)
    except (httpx.HTTPError, httpx.InvalidURL) as error:
        # The message is the error's class, not its text: a bad address can carry the key in it.
        log.warning("Could not send a ticket click event to PostHog (%s)", type(error).__name__)


def track_payload(api_key: str, event: TrackEvent, environment: str, device: str) -> dict:
    """An event from the app. The session id is the only identity: random, kept in the app's memory, no person profile."""
    properties: dict = {"environment": environment, "device": device, "$process_person_profile": False, "$geoip_disable": True}
    for name in ("show_key", "show_name", "venue", "filter", "filters", "when", "value"):
        if getattr(event, name) is not None:
            properties[name] = getattr(event, name)
    return {"api_key": api_key, "event": event.event, "distinct_id": event.session_id, "properties": properties}


def forward_track(event: TrackEvent, device: str, post: Post = httpx.post) -> None:
    """Sends an app event to PostHog. Never raises over the network, like forward_ticket_click."""
    config = posthog_config()
    if config is None:
        return
    api_key, host = config
    try:
        post(f"{host}{CAPTURE_PATH}", json=track_payload(api_key, event, environment_name(), device), timeout=TIMEOUT_SECONDS).raise_for_status()
    except httpx.HTTPStatusError as error:
        log.warning("PostHog refused an app event: HTTP %s", error.response.status_code)
    except (httpx.HTTPError, httpx.InvalidURL) as error:
        log.warning("Could not send an app event to PostHog (%s)", type(error).__name__)
