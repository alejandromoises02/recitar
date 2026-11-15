"""Where a ticket click goes and what is kept about it (see GET /go/{event_id})."""

from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple
from urllib.parse import urlsplit, urlunsplit

from app.domain.event import Event

UTM_SOURCE = "recitar"

# Where in the app a click came from; anything else is stored as "other", so a wrong value never blocks a purchase.
KNOWN_SOURCES = ("show", "spotlight")
OTHER_SOURCE = "other"

# Crawlers, link previews and scripts: sent on to the ticket page like anyone, but not counted as interest.
_BOT_MARKERS = ("bot", "crawl", "spider", "slurp", "preview", "facebookexternalhit", "whatsapp", "telegram", "headless", "python-requests", "curl/", "wget", "httpclient")


@dataclass(frozen=True)
class TicketClick:
    show_key: str
    event_id: str
    vendor: str | None  # the ticketer used; None when the date has no link and the visitor went to the source page
    source: str
    at: datetime


class Destination(NamedTuple):
    url: str
    vendor: str | None


def source_of(asked: str | None) -> str:
    """The place the click came from: "show" when the app did not say, "other" when it said something unknown."""
    if asked is None:
        return "show"
    return asked if asked in KNOWN_SOURCES else OTHER_SOURCE


def _is_web_url(url: str) -> bool:
    """An http(s) link with a host and nothing a browser and a parser could read differently: a backslash,
    or a user name before the host (`https://trusted.example@evil.example`), which no ticketer uses."""
    if "\\" in url:
        return False
    parts = urlsplit(url)
    return parts.scheme in ("http", "https") and bool(parts.netloc) and "@" not in parts.netloc


def destination(event: Event, vendor: str | None) -> Destination | None:
    """The link of the asked vendor, else the first one, else the show's page at its source. Always one the
    scrapers stored for this event and always http(s): never something the request carries."""
    links = [link for link in event.ticket_links if _is_web_url(link.url)]
    chosen = next((link for link in links if vendor is not None and link.vendor == vendor), links[0] if links else None)
    if chosen is not None:
        return Destination(chosen.url, chosen.vendor)
    return Destination(event.source_url, None) if _is_web_url(event.source_url) else None


def with_utm_source(url: str) -> str:
    """The link with `utm_source=recitar`: replaced where the link already has one, else appended. The
    rest of the query is kept byte for byte, so the ticketer's own parameters are not re-encoded."""
    parts = urlsplit(url)
    ours = f"utm_source={UTM_SOURCE}"
    query, replaced = [], False
    for pair in parts.query.split("&") if parts.query else []:
        if pair.split("=", 1)[0] != "utm_source":
            query.append(pair)
        elif not replaced:
            query.append(ours)
            replaced = True
    if not replaced:
        query.append(ours)
    return urlunsplit(parts._replace(query="&".join(query)))


def looks_like_bot(user_agent: str | None) -> bool:
    """Browsers always say who they are, so a missing agent is a script."""
    if not user_agent:
        return True
    agent = user_agent.lower()
    return any(marker in agent for marker in _BOT_MARKERS)
