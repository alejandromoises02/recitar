"""Scraper for Coolco, from the pages its own shop renders (a Palco4 shop, also served as cc-ar.palco4.com).

What 2026-11-17 showed:
- the main page (/tickets-ar/es/main) has one card per show linking /tickets-ar/<language>/<slug>:
  9 shows, all at Estadio Obras Sanitarias. /lista redirects to it and /en/main lists the same 9;
  cc-ar.palco4.com's main is another channel that lists none. There is no sitemap. Show pages also
  answer at /evento?idEvento=<n>: every id from 195 to 232 that main does not link gave no show
  (a redirect or an empty page), so main listed everything;
- a show's page holds its performances in the JSON of `event_sessions_list_widget_Sessions_...`
  (lists of sessions, each with `fechaCelebracion` with its offset and `litEvento`, the title without
  the venue the page's <title> appends), and its venue in `dataLayerP4` (name, city "CABA", state).
  A sold-out session has no tickets left (aforo minus sold, reserved and blocked) and is kept.
  A show whose sale has not opened has no sessions (LP on 2026-11-24, presale two days later): its
  page still announces its title and first date in `event_sessions_list_widget_event_...`, used then;
- an unknown slug redirects to main. Cloudflare answered 200, with no challenge, to our User-Agent.
  robots.txt allows everything to `*` with `Content-Signal: search=yes, ai-train=no`: a listing that
  links to the official page is search.
"""

import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name, plain, region_code
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://ticketing.coolco.io"
MAIN = "/tickets-ar/es/main"
SHOW = "/tickets-ar/es/"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Coolco"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
MAX_SHOW_PAGES = 100  # 9 shows on 2026-11-17

_CARD = re.compile(r"""window\.location\.href='(?:https?://[^/']+)?/tickets-ar/(?:es|en)/([a-z0-9-]+)'""")
_SESSIONS = re.compile(r"event_sessions_list_widget_Sessions_\$\{\w+\}`\]\s*=\s*")
_DATA_LAYER = re.compile(r"var dataLayerP4\s*=\s*")
_ANNOUNCED = re.compile(r"event_sessions_list_widget_event_\$\{\w+\}`\]\.(title|startDate) = `([^`]*)`")
_OG_IMAGE = re.compile(r'<meta property="og:image" content="([^"]+)"')


class ListingTooLongError(RuntimeError):
    """More show pages than expected: stop rather than store part of them."""


def show_slugs(page: str) -> set[str]:
    """The shows the main page's cards link to."""
    return set(_CARD.findall(page))


def _json_after(pattern: re.Pattern, page: str) -> object:
    for match in pattern.finditer(page):
        try:
            return json.JSONDecoder().raw_decode(page, match.end())[0]
        except ValueError:
            continue
    return None


def _sessions(page: str) -> list[dict]:
    groups = _json_after(_SESSIONS, page)
    if not isinstance(groups, list):
        return []
    flat = [s for group in groups for s in (group if isinstance(group, list) else [group])]
    return [s for s in flat if isinstance(s, dict)]


def _announced(page: str) -> list[dict]:
    """A show whose sale has not opened has no sessions yet, but its page announces its title and first
    date (local time, as LP's on 2026-11-24): taken as one session in the shape of the real ones."""
    fields = dict(_ANNOUNCED.findall(page))
    if not fields.get("title") or not fields.get("startDate"):
        return []
    try:
        starts_at = datetime.fromisoformat(fields["startDate"]).replace(tzinfo=BA)
    except ValueError:
        return []
    return [{"litEvento": fields["title"], "fechaCelebracion": starts_at.isoformat()}]


def region_of(city: str, state: str) -> str | None:
    """Palco4 writes the city as "CABA" with state "Buenos Aires", which region_code reads as the province."""
    if plain(city) in {"caba", "capital federal"}:
        return CITY_OF_BUENOS_AIRES
    return region_code(city, state)


def parse_show(page: str, slug: str, *, now: datetime) -> list[Event]:
    """One event per performance of the show at `slug` that has not started yet."""
    layer = _json_after(_DATA_LAYER, page)
    layer = layer if isinstance(layer, dict) else {}
    venue = clean_text(layer.get("venue") or "")
    if not venue:
        return []
    city, state = clean_text(layer.get("venueCity") or ""), clean_text(layer.get("venueState") or "")
    region = region_of(city, state)
    image = _OG_IMAGE.search(page)
    url = f"{SITE}{SHOW}{slug}"
    events = []
    for session in _sessions(page) or _announced(page):
        title = clean_text(session.get("litEvento") or "")
        when = session.get("fechaCelebracion")
        if not title or not isinstance(when, str):
            continue
        starts_at = datetime.fromisoformat(when.split("[", 1)[0]).astimezone(BA)
        if starts_at < now:
            continue
        events.append(Event(
            id=f"coolco-{slug}-{starts_at:%Y%m%dT%H%M}",
            category=provisional_category(title, starts_at),
            title=title,
            venue=venue,
            city=city_name(city or None, region),
            region=region,
            country="AR",
            starts_at=starts_at,
            ticket_links=[TicketLink(vendor=VENDOR, url=url)],
            source_url=url,
            **source_image(image.group(1) if image else None),
            updated_at=now,
        ))
    return events


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Read the main page, then each show it links, pausing `delay` seconds between requests. A main
    page that fails stops the scrape (the runner reports it); a show that fails is skipped."""
    now = datetime.now(tz=BA)
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:
        slugs = sorted(show_slugs(client.get(SITE + MAIN).raise_for_status().text))
        time.sleep(delay)
        if len(slugs) > MAX_SHOW_PAGES:
            raise ListingTooLongError(f"more than {MAX_SHOW_PAGES} show pages; raise MAX_SHOW_PAGES")
        for slug in slugs:
            try:
                response = client.get(SITE + SHOW + slug)
            except httpx.HTTPError:
                response = None
            time.sleep(delay)
            if response is not None and response.status_code == 200:
                events += parse_show(response.text, slug, now=now)
    return events if regions is None else [e for e in events if e.region in regions]
