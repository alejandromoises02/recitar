"""Scraper for Ticketek Argentina, through the JSON APIs its own site reads.

The site is an AngularJS app whose pages are all the same empty shell, so the data comes from:
- the search API with an empty query, which lists every show in the country page by page
  (`siguiente` is the next page, missing on the last one; pages can be short or even empty).
  Filtering it by province looks equivalent but is not: on 2026-11-16 it missed a show on sale
  (Divididos at Bendu Arena) that the empty query and the venue's own page both listed;
- the node API, one answer per show, whose `google_structured_data` holds one schema.org MusicEvent
  per performance. Its `data-performances` timestamps are local times stored as UTC (three hours
  off) and include passes that are not performances, so they are not used.

A listing entry without a venue in its path ("hairspray") is an artist page: it links to its shows.
robots.txt allows everything but /websource/ (the checkout), which is never fetched, only linked.
"""

import json
import re
import time
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.dates import time_given
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name, plain, region_code
from app.scrapers.images import first_image_url, source_image
from app.scrapers.text import clean_text

SITE = "https://www.ticketek.com.ar"
SEARCH_API = "https://prod-cms-search.ticketek.com.ar/api/1.1/"
NODE_API = "https://prod-cms-api.ticketek.com.ar/api/1.0/node"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Ticketek"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
# Where to show events: the scraper reads the whole country, then keeps these regions.
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
LISTING_START = "search/%20"  # an empty query: what the site's search answers with everything
MAX_PAGES = 60  # the whole country took 14 pages on 2026-11-16

# Ticketek's own categories. Specials (talks, dinner shows, exhibitions) and family shows are stage
# shows, so theatre. Sports are not shows; anything unlisted is "other".
_CATEGORIES: dict[str, EventCategory | None] = {
    "musica": "concert", "internacionales": "concert", "teatro": "theatre",
    "especiales": "theatre", "familia": "theatre", "deportes": None,
}

# The 48 barrios of the city, plus names Ticketek uses for it. Ticketek files many city venues under
# the province "Buenos Aires"; their locality is how they are told apart. "San Nicolás" alone is left
# out: it is also a city of the province, and Ticketek writes the barrio as "Barrio San Nicolás".
_CITY_LOCALITIES = frozenset(plain(name) for name in (
    "Agronomía", "Almagro", "Balvanera", "Barracas", "Belgrano", "Boedo", "Caballito", "Chacarita",
    "Coghlan", "Colegiales", "Constitución", "Flores", "Floresta", "La Boca", "La Paternal", "Liniers",
    "Mataderos", "Monte Castro", "Montserrat", "Nueva Pompeya", "Núñez", "Palermo", "Parque Avellaneda",
    "Parque Chacabuco", "Parque Chas", "Parque Patricios", "Puerto Madero", "Recoleta", "Retiro",
    "Saavedra", "San Cristóbal", "San Telmo", "Vélez Sarsfield", "Versalles", "Villa Crespo",
    "Villa del Parque", "Villa Devoto", "Villa General Mitre", "Villa Lugano", "Villa Luro",
    "Villa Ortúzar", "Villa Pueyrredón", "Villa Real", "Villa Riachuelo", "Villa Santa Rita",
    "Villa Soldati", "Villa Urquiza", "CABA", "Microcentro",
))
_BARRIO = re.compile(r"^barrio\s+")


class ListingTooLongError(RuntimeError):
    """The listing has more pages than expected: stop rather than store part of it."""


def region_of(state: str, city: str) -> str | None:
    """ISO region of a Ticketek venue from its `state` and `city` fields."""
    place = plain(city or "")
    if plain(state or "") == "buenos aires" and (_BARRIO.match(place) or place in _CITY_LOCALITIES):
        return CITY_OF_BUENOS_AIRES
    return region_code(city or "", state or "")


def node_url(path: str) -> str:
    """The same URL the site's node factory builds: the first "/" becomes "--", then all is encoded."""
    return NODE_API + quote(("?path=" + path).replace("/", "--", 1), safe="")


def listing_url(relative: str) -> str:
    """A listing page's URL. `siguiente` comes with a raw space ("search/ ?pagina=1"), which must be encoded."""
    return SEARCH_API + quote(relative, safe="/?=&%")


def listing_page(page: dict) -> tuple[list[str], str | None]:
    """The show paths on one search page, and the next page (relative to SEARCH_API), if any."""
    paths = [entry["url"] for entry in page.get("resultados") or [] if isinstance(entry, dict) and entry.get("url")]
    return paths, page.get("siguiente") or None


def _widgets(node: dict) -> list[dict]:
    zones = node.get("widgets") or {}
    return [w for zone in zones.values() if isinstance(zone, list) for w in zone if isinstance(w, dict)]


def artist_show_paths(node: dict) -> list[str]:
    """The shows an artist page links to."""
    return [
        show["link"]
        for widget in _widgets(node) if widget.get("type") == "tkt-artist-shows"
        for show in widget.get("shows") or [] if isinstance(show, dict) and show.get("link")
    ]


def _music_events(node: dict) -> list[dict]:
    data = node.get("google_structured_data") or []
    items = data if isinstance(data, list) else [data]
    return [i for i in items if isinstance(i, dict) and i.get("@type") in ("MusicEvent", "Event") and i.get("startDate")]


def _category(node: dict, title: str, starts_at: datetime) -> EventCategory | None:
    parent = plain(((node.get("category") or {}).get("parent")) or "")
    category = _CATEGORIES.get(parent, "other")
    return provisional_category(title, starts_at) if category == "concert" else category


def _canceled(node: dict) -> bool:
    """The buy button says "Cancelado" (state "canceled"); the MusicEvent entries stay as they were."""
    return any(w.get("type") == "tkt-show-buy" and w.get("state") == "canceled" for w in _widgets(node))


def parse_show(node: dict, path: str, now: datetime) -> list[Event]:
    """One event per performance of the show at `path` that has not started yet; none if it was canceled."""
    title = clean_text(node.get("title") or "")
    venue = node.get("venue") or {}
    if not title or not isinstance(venue, dict) or not venue.get("title") or _canceled(node):
        return []
    page = f"{SITE}/{path}"
    region = region_of(venue.get("state") or "", venue.get("city") or "")
    events = []
    for item in _music_events(node):
        starts_at = datetime.fromisoformat(item["startDate"])
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=BA)
        if starts_at < now:
            continue
        category = _category(node, title, starts_at)
        if category is None:
            return []
        artist = (node.get("artist") or {}).get("title") if category == "concert" else None
        offer = (item.get("offers") or {}).get("url")
        link = offer if isinstance(offer, str) and offer.startswith(SITE + "/") else page
        events.append(Event(
            id=f"ticketek-{path.replace('/', '-')}-{starts_at:%Y%m%dT%H%M}",
            category=category,
            title=title,
            artist=clean_text(artist) if artist else None,
            venue=clean_text(venue["title"]),
            city=city_name(venue.get("city"), region),
            region=region,
            country="AR" if plain(venue.get("country") or "") == "argentina" else None,
            starts_at=starts_at,
            time_known=time_given(item["startDate"]),
            ticket_links=[TicketLink(vendor=VENDOR, url=link)],
            source_url=page,
            **source_image(first_image_url(item.get("image"))),
            updated_at=now,
        ))
    return events


def _json(response: httpx.Response) -> dict | None:
    """The node API answers JSON as application/octet-stream."""
    if response.status_code != 200:
        return None
    try:
        data = json.loads(response.content)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Walk the whole listing, then read each show, pausing `delay` seconds between requests.
    A listing page that fails stops the scrape (the runner reports it); a show that fails is skipped."""
    now = datetime.now(tz=BA)
    paths: list[str] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, follow_redirects=True, transport=transport) as client:
        relative: str | None = LISTING_START
        visited: set[str] = set()
        for _ in range(MAX_PAGES):
            if relative is None or relative in visited:
                break
            visited.add(relative)
            page = client.get(listing_url(relative)).raise_for_status().json()
            found, relative = listing_page(page)
            paths += [p for p in found if p not in paths]
            time.sleep(delay)
        if relative is not None and relative not in visited:
            raise ListingTooLongError(f"the listing goes on past {MAX_PAGES} pages; raise MAX_PAGES")
        events: list[Event] = []
        done: set[str] = set()
        while paths:
            path = paths.pop(0)
            if path in done:
                continue
            done.add(path)
            node = _json(client.get(node_url(path)))
            time.sleep(delay)
            if node is None:
                continue
            if node.get("type") == "artist":
                paths += [p for p in artist_show_paths(node) if p not in done]
                continue
            events += parse_show(node, path, now)
    return events if regions is None else [e for e in events if e.region in regions]
