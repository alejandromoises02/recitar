"""Scraper for TuEntrada, from the pages its own Next.js site renders.

Every page carries its data in the React Server Components payload (`self.__next_f.push` scripts):
- the search page lists shows a few at a time. An empty search is refused, so the listing is a date
  range from today on; on 2026-11-17 it gave the same 143 entries ending in 2028 or 2035. Its pages
  are linked by a "Go to next page" anchor carrying a cursor. The sitemap adds nothing: on that day,
  of its 282 URLs missing from the listing, 257 were venue pages and 25 answered "Página no encontrada";
- a show's page holds `eventSessions`, one per performance, and its venue's coordinates;
- the category exists only as a search filter (`?categoria=`), so each category is listed separately
  and a show takes the categories it was listed under.

Sessions name a city but no province. Georef, the Argentine government's geography API, gives it:
- from the venue's coordinates, when the page has the venue's own entry. Without it, the page's map
  points at the Obelisco (-34.6037, -58.3816) whatever the venue: on 2026-11-17, 29 of 143 shows did,
  from Escobar to Neuquén, so the map's coordinates are never used;
- otherwise from the city, when the city already says the region ("Buenos Aires", "Neuquén");
- otherwise from the city's name, when every locality of that name is in the same province
  ("Belén De Escobar"). An ambiguous name ("Ituzaingó" is in Buenos Aires and Corrientes) stays unknown.
robots.txt allows everything.
"""

import html as html_lib
import json
import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import city_name, plain, region_code
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://www.tuentrada.com"
GEOREF = "https://apis.datos.gob.ar/georef/api"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "TuEntrada"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
HORIZON = timedelta(days=3 * 365)  # the listing ends at this date; nothing was on sale past 2028
MAX_PAGES = 100  # the whole listing took 24 pages on 2026-11-17

# TuEntrada's categories, as its search takes them. "jazz/blues" is not inside "música"; "musical" is,
# and is mostly concerts. Family shows are stage shows, so theatre. Sports are not shows. Anything
# else, or a show under no category (cinema, ballet, fairs), is "other".
_CATEGORIES: dict[str, EventCategory | None] = {
    "música": "concert", "jazz/blues": "concert", "festivales de música": "concert",
    "teatro": "theatre", "familia": "theatre", "deportes": None,
}

_PUSH = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')
_NEXT = re.compile(r'<a[^>]*aria-label="Go to next page"[^>]*href="([^"]*)"|<a[^>]*href="([^"]*)"[^>]*aria-label="Go to next page"')
# the venue's own entry; the map component also has coordinates, but a placeholder when the venue has none
_VENUE_COORDINATES = re.compile(
    r'"item":\{"id":\d+,"name":"[^"]*","slug":"[^"]*","latitude":"(-?\d+(?:\.\d+)?)","longitude":"(-?\d+(?:\.\d+)?)"'
)


class ListingTooLongError(RuntimeError):
    """The listing has more pages than expected: stop rather than store part of it."""


def payload(page: str) -> str:
    """The page's Server Components payload, joined back into one string."""
    return "".join(json.loads(chunk) for chunk in _PUSH.findall(page))


def _value_after(data: str, key: str) -> object | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*', data)
    if match is None:
        return None
    try:
        return json.JSONDecoder().raw_decode(data, match.end())[0]
    except ValueError:
        return None


def listing_url(path: str) -> str:
    return SITE + path


def date_listing_path(today: datetime) -> str:
    return f"/busqueda?desde={today:%d-%m-%Y}&hasta={today + HORIZON:%d-%m-%Y}"


def category_listing_path(category: str) -> str:
    return "/busqueda?categoria=" + quote(category, safe="")


def listing_page(page: str) -> tuple[list[dict], str | None]:
    """The entries on one search page, and the path of the next page, if any (the last one links to "#")."""
    entries = _value_after(payload(page), "events")
    match = _NEXT.search(page)
    following = html_lib.unescape(match.group(1) or match.group(2)) if match else None
    found = [e for e in entries if isinstance(e, dict) and e.get("slug")] if isinstance(entries, list) else []
    return found, following if following and following.startswith("/busqueda") else None


def coordinates(page: str) -> tuple[float, float] | None:
    """The venue's coordinates, when the page has the venue's own entry."""
    match = _VENUE_COORDINATES.search(payload(page))
    return (float(match.group(1)), float(match.group(2))) if match else None


def region_of(city: str, province: str | None) -> str | None:
    """ISO region from Georef's province name, or from the city when there is none."""
    return region_code("", province) if province else region_code(city or "", "")


def category_of(listed_under: set[str], title: str, starts_at: datetime) -> EventCategory | None:
    kinds = {_CATEGORIES.get(name, "other") for name in listed_under} or {"other"}
    if None in kinds:
        return None
    if "concert" in kinds:
        return provisional_category(title, starts_at)
    return "theatre" if "theatre" in kinds else "other"


def parse_show(
    page: str, slug: str, *, listed_under: set[str], image: str | None, province: str | None, now: datetime
) -> list[Event]:
    """One event per performance at `slug` that has not started yet. Passes ("Abono") are not performances."""
    sessions = _value_after(payload(page), "eventSessions")
    if not isinstance(sessions, list):
        return []
    url = f"{SITE}/{slug}"
    events = []
    for session in sessions:
        if not isinstance(session, dict) or session.get("type") != "SESSION" or session.get("status") != "READY":
            continue
        title, venue = clean_text(session.get("name") or ""), clean_text(session.get("venue") or "")
        if not title or not venue or not session.get("date"):
            continue
        starts_at = datetime.fromisoformat(session["date"])
        if starts_at < now:
            continue
        category = category_of(listed_under, title, starts_at)
        if category is None:
            return []
        region = region_of(session.get("city") or "", province)
        events.append(Event(
            id=f"tuentrada-{slug}-{starts_at:%Y%m%dT%H%M}",
            category=category,
            title=title,
            venue=venue,
            city=city_name(clean_text(session.get("city") or "") or None, region),
            region=region,
            country="AR",
            starts_at=starts_at,
            time_known=not session.get("dateStartUnconfirmed"),
            ticket_links=[TicketLink(vendor=VENDOR, url=url)],
            source_url=url,
            **source_image(image),
            updated_at=now,
        ))
    return events


def _georef(client: httpx.Client, path: str, params: dict) -> dict | None:
    try:
        response = client.get(f"{GEOREF}/{path}", params=params)
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    return data if response.status_code == 200 and isinstance(data, dict) else None


def province_at(client: httpx.Client, point: tuple[float, float]) -> str | None:
    """The province Georef places these coordinates in; None when it cannot say."""
    data = _georef(client, "ubicacion", {"lat": point[0], "lon": point[1]}) or {}
    name = ((data.get("ubicacion") or {}).get("provincia") or {}).get("nombre")
    return name if isinstance(name, str) else None


def province_named(client: httpx.Client, city: str) -> str | None:
    """The province of every Argentine locality called `city`; None when there are several, or none."""
    data = _georef(client, "localidades", {"nombre": city, "campos": "provincia.nombre", "max": 100}) or {}
    localities = data.get("localidades")
    names = {((l.get("provincia") or {}).get("nombre")) for l in localities if isinstance(l, dict)} if isinstance(localities, list) else set()
    return names.pop() if len(names) == 1 and None not in names else None


def session_city(page: str) -> str:
    sessions = _value_after(payload(page), "eventSessions")
    first = sessions[0] if isinstance(sessions, list) and sessions and isinstance(sessions[0], dict) else {}
    return clean_text(first.get("city") or "")


def province_of(client: httpx.Client, page: str, known: dict[object, str | None]) -> str | None:
    """The province of the show's venue (see the module docstring), asked once per venue or city."""
    point, city = coordinates(page), session_city(page)
    key: object = point or plain(city)
    if key not in known:
        if point is not None:
            known[key] = province_at(client, point)
        elif region_of(city, None) is not None:
            known[key] = None  # the city alone says it
        else:
            known[key] = province_named(client, city) if city else None
    return known[key]


def _walk(client: httpx.Client, path: str, delay: float) -> list[dict]:
    entries: list[dict] = []
    following: str | None = path
    visited: set[str] = set()
    for _ in range(MAX_PAGES):
        if following is None or following in visited:
            return entries
        visited.add(following)
        found, following = listing_page(client.get(listing_url(following)).raise_for_status().text)
        entries += found
        time.sleep(delay)
    if following is not None and following not in visited:
        raise ListingTooLongError(f"{path} goes on past {MAX_PAGES} pages; raise MAX_PAGES")
    return entries


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """List every show, then each category, then read each show's page, pausing `delay` seconds between
    requests. A listing page that fails stops the scrape (the runner reports it); a show that fails is skipped."""
    now = datetime.now(tz=BA)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:
        shows = {e["slug"]: e for e in _walk(client, date_listing_path(now), delay) if e.get("model") == "event"}
        listed_under: dict[str, set[str]] = {}
        for category in _CATEGORIES:
            for entry in _walk(client, category_listing_path(category), delay):
                listed_under.setdefault(entry["slug"], set()).add(category)
        provinces: dict[object, str | None] = {}
        events: list[Event] = []
        for slug, entry in shows.items():
            response = client.get(f"{SITE}/{quote(slug, safe='')}")  # a gone show redirects home: not followed
            time.sleep(delay)
            if response.status_code != 200:
                continue
            events += parse_show(
                response.text, slug,
                listed_under=listed_under.get(slug, set()),
                image=(entry.get("imageMainNew") or {}).get("src"),
                province=province_of(client, response.text, provinces),
                now=now,
            )
    return events if regions is None else [e for e in events if e.region in regions]
