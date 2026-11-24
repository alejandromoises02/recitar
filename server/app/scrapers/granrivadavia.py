"""Scraper for Teatro Gran Rivadavia (granrivadavia.com.ar), from the pages its own site renders.

The theatre sells through Fullticket, whose shop answers 403 (a Cloudflare challenge) to every
request without a browser; the theatre's site does not. What 2026-11-24 showed:
- /cartelera/ links one page per show as /evento/<n>/<slug> (3 shows; /inicio/ lists the same);
- a show's page has its title in `destacado-titulo`, its performances under "FUNCIONES" as
  "16.abr.27 / 21.00", its image at /imagenes/eventos/<n>.jpg and a "COMPRAR ENTRADAS" button to
  its Fullticket page, whose path says the kind of show ("entradas-musica-europe",
  "entradas-teatro-canticuenticos");
- a show's page answers at its path with a trailing slash; without it, a 302 to the slash form over
  plain http. An unknown show answers 200 with an empty title; /evento/<n> without a slug answers 404. Past
  shows keep their pages. robots.txt is a 404: no rules.
Every show is at the theatre itself (Av. Rivadavia 8636, City of Buenos Aires).
"""

import re
import time
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://www.granrivadavia.com.ar"
LISTING = "/cartelera/"
USER_AGENT = "recitAR-research/0.1"
VENUE = "Teatro Gran Rivadavia"
VENDOR = "Fullticket"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
MAX_EVENT_PAGES = 100  # 3 shows on 2026-11-24

_EVENT_PATH = re.compile(r'href="(/evento/(\d+)/[^"/]+)"')
_TITLE = re.compile(r'id="destacado-titulo">(.*?)</div>', re.S)
_PERFORMANCES = re.compile(r'id="fecha">FUNCIONES</span>(.*?</div>)\s*</div>\s*</div>', re.S)
_PERFORMANCE = re.compile(r">\s*(\d{1,2})\.([a-z]{3})\.(\d{2})(?:\s*/\s*(\d{1,2})\.(\d{2}))?\s*<")
_TICKETS = re.compile(r'href="(https://(?:www\.)?fullticket\.com/tickets/[^"]+)"')
_IMAGE = re.compile(r'src="(/imagenes/eventos/\d+\.jpg)"')
_MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


class ListingTooLongError(RuntimeError):
    """More show pages than expected: stop rather than store part of them."""


def event_paths(page: str) -> list[str]:
    """The show pages the cartelera links, in order, once each."""
    return list(dict.fromkeys(path for path, _ in _EVENT_PATH.findall(page)))


def _category(tickets: str | None, title: str, starts_at: datetime) -> EventCategory:
    if tickets and "/entradas-teatro-" in tickets:
        return "theatre"
    if tickets and "/entradas-musica-" not in tickets:
        return "other"
    return provisional_category(title, starts_at)


def _performances(page: str) -> list[tuple[datetime, bool]]:
    block = _PERFORMANCES.search(page)
    found = []
    for day, month, year, hour, minute in _PERFORMANCE.findall(block[1] if block else ""):
        if month not in _MONTHS:
            continue
        clock = (int(hour), int(minute)) if hour else (0, 0)
        found.append((datetime(2000 + int(year), _MONTHS[month], int(day), *clock, tzinfo=BA), bool(hour)))
    return found


def parse_event(page: str, path: str, *, now: datetime) -> list[Event]:
    """One event per performance of the show at `path` that has not started yet."""
    match = _TITLE.search(page)
    title = clean_text(unescape(match[1])) if match else ""
    if not title:
        return []
    number = _EVENT_PATH.search(f'href="{path}"')
    if not number:
        return []
    url = f"{SITE}{path}/"
    tickets = _TICKETS.search(page)
    ticket_url = tickets[1] if tickets else None
    link = TicketLink(vendor=VENDOR, url=ticket_url) if ticket_url else TicketLink(vendor=VENUE, url=url)
    image = _IMAGE.search(page)
    events: dict[str, Event] = {}
    for starts_at, time_known in _performances(page):
        if (starts_at < now) if time_known else (starts_at.date() < now.date()):
            continue
        event_id = f"granrivadavia-{number[2]}-{starts_at:%Y%m%dT%H%M}"
        events.setdefault(event_id, Event(
            id=event_id,
            category=_category(ticket_url, title, starts_at),
            title=title,
            venue=VENUE,
            city=city_name(None, CITY_OF_BUENOS_AIRES),
            region=CITY_OF_BUENOS_AIRES,
            country="AR",
            starts_at=starts_at,
            time_known=time_known,
            ticket_links=[link],
            source_url=url,
            **source_image(SITE + image[1] if image else None),
            updated_at=now,
        ))
    return list(events.values())


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES,
    delay: float = 2.0,
    transport: httpx.BaseTransport | None = None,
    now: datetime | None = None,
) -> list[Event]:
    """Read the cartelera, then each show it links, pausing `delay` seconds between requests. A
    cartelera that fails stops the scrape (the runner reports it); a show that fails is skipped."""
    now = now or datetime.now(tz=BA)
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:
        paths = event_paths(client.get(SITE + LISTING).raise_for_status().text)
        time.sleep(delay)
        if len(paths) > MAX_EVENT_PAGES:
            raise ListingTooLongError(f"more than {MAX_EVENT_PAGES} show pages; raise MAX_EVENT_PAGES")
        for path in paths:
            try:
                response = client.get(f"{SITE}{path}/")
            except httpx.HTTPError:
                response = None
            time.sleep(delay)
            if response is not None and response.status_code == 200:
                events += parse_event(response.text, path, now=now)
    return events if regions is None else [e for e in events if e.region in regions]
