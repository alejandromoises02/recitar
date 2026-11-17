"""Scraper for All Access, from the pages its own site renders (a Crowder shop).

The site's JSON API asks for an AWS WAF token, so it is not used. What lists the shows:
- the home, which links a curated selection, including shows announced without dates yet;
- the search page (/list/<text>), which matches titles, venues and descriptions but shows at most 50
  results, in alphabetical order and without pages. One search per letter and digit covers what
  fits; on 2026-11-17 a search refined to 2-4 letters wherever 50 came back (764 queries) found
  nothing more;
- each venue's page (/venue/<link>), which lists every show of that venue, past the search's cap.
Each show's page holds its data in `App.bootstrapData`: the venue with its address and coordinates,
and one entry per performance (UTC dates). The site gives no category. Passes ("Abono") have no
date, and the same show can be listed twice (a VIP package, a bank's presale): one is kept.
A slug that is not a show answers 200 with an empty page. robots.txt disallows nothing.
"""

import json
import re
import string
import time
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name, plain, region_code
from app.scrapers.georef import province_at
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://www.allaccess.com.ar"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "All Access"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
SEARCHES = string.ascii_lowercase + string.digits
MAX_SHOW_PAGES = 600  # 104 shows on 2026-11-17

_SLUG = re.compile(r"""["'](?:https?://(?:www\.)?allaccess\.com\.ar)?/event/([^'"/?#\s]+)""")
_BOOTSTRAP = re.compile(r"App\.bootstrapData\(")
_CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b")
# What the shop also sells under a show's name, and is not a show.
_NOT_A_SHOW = re.compile(r"\b(estacionamiento|parking|dine|hospitality)\b")


class ListingTooLongError(RuntimeError):
    """More show pages than expected: stop rather than store part of them."""


def event_slugs(page: str) -> set[str]:
    """The shows a home, search or venue page links to."""
    return set(_SLUG.findall(page))


def event_data(page: str) -> dict | None:
    """The show's own data on its page; None when the page holds no show."""
    for match in _BOOTSTRAP.finditer(page):
        try:
            data = json.JSONDecoder().raw_decode(page, match.end())[0]
        except ValueError:
            continue
        model = data.get("model") if isinstance(data, dict) else None
        if isinstance(model, dict) and (model.get("summary") or {}).get("model") == "event":
            return model.get("data") if isinstance(model.get("data"), dict) else None
    return None


def _address(data: dict) -> dict:
    return ((data.get("venue") or {}).get("address")) or {}


def venue_link(data: dict) -> str | None:
    link = (data.get("venue") or {}).get("link")
    return link if isinstance(link, str) and link else None


def coordinates(data: dict) -> tuple[float, float] | None:
    address = _address(data)
    lat, lon = address.get("latitude"), address.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or (lat, lon) == (0, 0):
        return None
    return float(lat), float(lon)


def region_of(city: str | None, province: str | None) -> str | None:
    """ISO region from the address as All Access writes it: "CABA" in the city wins (Huracán comes as
    city "CABA", province "Buenos Aires"); a city like "San Isidro, Buenos Aires" carries its province."""
    city, province = city or "", province or ""
    if plain(city) == "caba" or plain(province) == "caba":
        return CITY_OF_BUENOS_AIRES
    if not province and "," in city:
        city, province = (part.strip() for part in city.rsplit(",", 1))
    return region_code(city, province)


def parse_event(data: dict | None, slug: str, *, province: str | None, now: datetime) -> list[Event]:
    """One event per performance of the show at `slug` that has not started yet. `province` is
    Georef's name for where the venue is, if known; the address is used otherwise."""
    if not data:
        return []
    title, venue = clean_text(data.get("name") or ""), clean_text((data.get("venue") or {}).get("name") or "")
    if not title or not venue or _NOT_A_SHOW.search(plain(title)):
        return []
    address = _address(data)
    city = (address.get("city") or "").rsplit(",", 1)[0].strip() or None
    region = region_code("", province) if province else region_of(address.get("city"), address.get("province"))
    url = f"{SITE}/event/{slug}"
    events = []
    for show in data.get("shows") or []:
        if not isinstance(show, dict) or not show.get("startDate"):
            continue  # a pass ("Abono") has no date
        starts_at = datetime.fromisoformat(show["startDate"].replace("Z", "+00:00")).astimezone(BA)
        if starts_at < now:
            continue
        events.append(Event(
            id=f"allaccess-{slug}-{starts_at:%Y%m%dT%H%M}",
            category=provisional_category(title, starts_at),
            title=title,
            venue=venue,
            city=city_name(city, region),
            region=region,
            country="AR",
            starts_at=starts_at,
            time_known=bool(_CLOCK.search(show.get("name") or "")),  # "11/12/2026 21:00", not "Día 1"
            ticket_links=[TicketLink(vendor=VENDOR, url=url)],
            source_url=url,
            **source_image(data.get("thumbImage") or show.get("image")),
            updated_at=now,
        ))
    return events


def _one_per_performance(events: list[Event]) -> list[Event]:
    """The same show listed under several slugs is kept once, under its shortest slug."""
    kept: dict[tuple[str, datetime], Event] = {}
    for event in sorted(events, key=lambda e: len(e.id)):
        kept.setdefault((event.venue, event.starts_at.astimezone(UTC)), event)
    return [e for e in events if kept.get((e.venue, e.starts_at.astimezone(UTC))) is e]


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Read the home and one search per letter and digit, then each show, adding the shows of every
    venue met along the way, pausing `delay` seconds between requests. A listing page that fails
    stops the scrape (the runner reports it); a show that fails is skipped."""
    now = datetime.now(tz=BA)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:

        def listing(path: str) -> set[str]:
            found = event_slugs(client.get(SITE + path).raise_for_status().text)
            time.sleep(delay)
            return found

        queue: list[str] = sorted(listing("/"))
        for character in SEARCHES:
            queue += sorted(listing(f"/list/{character}") - set(queue))
        seen, venues = set(queue), set()
        provinces: dict[object, str | None] = {}
        events: list[Event] = []
        read = 0
        while queue:
            if read == MAX_SHOW_PAGES:
                raise ListingTooLongError(f"more than {MAX_SHOW_PAGES} show pages; raise MAX_SHOW_PAGES")
            slug = queue.pop(0)
            read += 1
            response = client.get(f"{SITE}/event/{slug}")
            time.sleep(delay)
            data = event_data(response.text) if response.status_code == 200 else None
            if data is None:
                continue
            link = venue_link(data)
            if link and link not in venues:
                venues.add(link)
                new = sorted(listing(f"/venue/{link}") - seen)
                seen.update(new)
                queue += new
            point = coordinates(data)
            key = point or (data.get("venue") or {}).get("name")
            if key not in provinces:
                provinces[key] = province_at(client, point) if point else None
            events += parse_event(data, slug, province=provinces[key], now=now)
    events = _one_per_performance(events)
    return events if regions is None else [e for e in events if e.region in regions]
