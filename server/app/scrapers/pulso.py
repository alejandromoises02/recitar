"""Scraper for Pulso Tickets (pulsotickets.com), from the pages its own site renders (Laravel + Livewire).

Found on 2026-11-17, when the site had one public event:
- robots.txt disallows nothing. There is no events index, sitemap or JSON API: /eventos, /events,
  /cartelera, /buscar, /api/eventos and /sitemap.xml answer 404, and the front-end bundle calls no
  listing endpoint. The home answers 302 to that one event (/evento/popfest-1015), with a body that
  links it too; www.pulsotickets.com redirects to the www form of the same path. A home listing
  several events could not be seen, so it is read as any page linking /evento/<slug>.
- The event page (/evento/<slug>) is ~2.3 MB of inline images and gives only the day, never the
  time. Its tickets page (/evento/<slug>/tickets, ~55 KB) has everything: the title (h1), one card
  per performance ("sáb., 05 dic. 2026 - 13:00 hs", with its own image), the venue with its address
  ("..., CABA") and a Google Maps link with its coordinates, and the site category in the analytics
  call ("Música & Recitales"). Only the tickets page is read; links point to the event page.
- An unknown slug answers 404 on the tickets page.
"""

import re
import time
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name, plain, region_code
from app.scrapers.georef import province_at
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://pulsotickets.com"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Pulso Tickets"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
MAX_EVENT_PAGES = 100  # 1 event on 2026-11-17

_SLUG = re.compile(r"""(?:https?://(?:www\.)?pulsotickets\.com)?/evento/([A-Za-z0-9][A-Za-z0-9_-]*)""")
_TITLE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
_PERFORMANCE = re.compile(r'<h3 class="[^"]*text-blue-700[^"]*">(.*?)</h3>', re.S)
_DATE = re.compile(r"(\d{1,2})\s+([a-z]{3,4})\.?,?\s+(\d{4})(?:\s*-\s*(\d{1,2}):(\d{2}))?")
_IMAGE = re.compile(r'src="(https://(?:www\.)?pulsotickets\.com/storage/funciones-images/[^"]+)"')
_VENUE = re.compile(r'<p class="text-xl font-bold text-slate-900">(.*?)</p>\s*<p class="text-slate-600[^"]*">(.*?)</p>', re.S)
_MAP = re.compile(r"google\.com/maps/search/\?api=1&(?:amp;)?query=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
_CATEGORY = re.compile(r"item_category:\s*'([^']*)'")
_TAG = re.compile(r"<[^>]+>")
_MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "sept": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
}


class ListingTooLongError(RuntimeError):
    """More event pages than expected: stop rather than store part of them."""


def event_slugs(page: str, location: str | None = None) -> list[str]:
    """The events a home links to, in order, once each; `location` is where a redirect points."""
    found = _SLUG.findall(location or "") + _SLUG.findall(page)
    return list(dict.fromkeys(found))


def _text(html: str) -> str:
    return clean_text(unescape(_TAG.sub(" ", html)))


def coordinates(page: str) -> tuple[float, float] | None:
    match = _MAP.search(page)
    return (float(match[1]), float(match[2])) if match else None


def region_of(address: str) -> str | None:
    """ISO region from the address's last part, as the site writes it ("..., CABA")."""
    parts = [part.strip() for part in address.split(",") if part.strip()]
    last = parts[-1] if len(parts) > 1 else ""
    if plain(last) == "caba":
        return CITY_OF_BUENOS_AIRES
    return region_code("", last) if last else None


def _category(page: str, title: str, starts_at: datetime) -> EventCategory:
    match = _CATEGORY.search(page)
    site = plain(unescape(match[1])) if match else ""
    if "musica" in site or "recital" in site:
        return provisional_category(title, starts_at)
    return "theatre" if "teatro" in site else "other"


def _starts_at(text: str) -> tuple[datetime, bool] | None:
    match = _DATE.search(plain(text))
    month = _MONTHS.get(match[2]) if match else None
    if not month:
        return None
    hour, minute = (int(match[4]), int(match[5])) if match[4] else (0, 0)
    return datetime(int(match[3]), month, int(match[1]), hour, minute, tzinfo=BA), bool(match[4])


def parse_event(page: str, slug: str, *, province: str | None, now: datetime) -> list[Event]:
    """One event per performance on the tickets page of `slug` that has not started yet. `province`
    is Georef's name for where the venue is, if known; the address is used otherwise."""
    title_match, venue_match = _TITLE.search(page), _VENUE.search(page)
    title = _text(title_match[1]) if title_match else ""
    venue = _text(venue_match[1]) if venue_match else ""
    if not title or not venue:
        return []
    region = region_code("", province) if province else region_of(_text(venue_match[2]))
    url = f"{SITE}/evento/{slug}"
    events: dict[str, Event] = {}
    previous_end = 0
    for performance in _PERFORMANCE.finditer(page):
        card, previous_end = page[previous_end:performance.start()], performance.end()
        when = _starts_at(_text(performance[1]))
        if when is None or when[0] < now:
            continue
        starts_at, time_known = when
        image = _IMAGE.findall(card)
        event_id = f"pulso-{slug}-{starts_at:%Y%m%dT%H%M}"
        events.setdefault(event_id, Event(
            id=event_id,
            category=_category(page, title, starts_at),
            title=title,
            venue=venue,
            city=city_name(None, region),
            region=region,
            country="AR",
            starts_at=starts_at,
            time_known=time_known,
            ticket_links=[TicketLink(vendor=VENDOR, url=url)],
            source_url=url,
            **source_image(image[-1] if image else None),
            updated_at=now,
        ))
    return list(events.values())


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Read the home, then each event's tickets page, pausing `delay` seconds after each request to
    the site. Redirects are not followed: the home's redirect is where its only event is named. A
    home that fails stops the scrape (the runner reports it); an event page that fails is skipped."""
    now = datetime.now(tz=BA)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:
        home = client.get(f"{SITE}/")
        time.sleep(delay)
        if not home.is_redirect:
            home.raise_for_status()
        slugs = event_slugs(home.text, home.headers.get("location") if home.is_redirect else None)
        if len(slugs) > MAX_EVENT_PAGES:
            raise ListingTooLongError(f"more than {MAX_EVENT_PAGES} event pages; raise MAX_EVENT_PAGES")
        provinces: dict[object, str | None] = {}
        events: list[Event] = []
        for slug in slugs:
            response = client.get(f"{SITE}/evento/{slug}/tickets")
            time.sleep(delay)
            if response.status_code != 200:
                continue
            point = coordinates(response.text)
            if point is not None and point not in provinces:
                provinces[point] = province_at(client, point)
            events += parse_event(response.text, slug, province=provinces.get(point), now=now)
    return events if regions is None else [e for e in events if e.region in regions]
