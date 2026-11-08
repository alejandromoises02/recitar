"""Scraper for Livepass: the public /t/show listing, then each event's schema.org JSON-LD."""

import json
import re
import time
import unicodedata
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.domain.event import Event, TicketLink

BASE_URL = "https://www.livepass.com.ar"
LISTING_PATH = "/t/show"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Livepass"
BA = ZoneInfo("America/Argentina/Buenos_Aires")

# Where to show events. The scraper stores every region; this is only the default filter.
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})

_COMUNA = re.compile(r"^comuna\s+\d+", re.I)

# ISO 3166-2:AR, keyed by accent-free lowercase province name.
_PROVINCES = {
    "salta": "AR-A", "buenos aires": "AR-B", "san luis": "AR-D", "entre rios": "AR-E",
    "la rioja": "AR-F", "santiago del estero": "AR-G", "chaco": "AR-H", "san juan": "AR-J",
    "catamarca": "AR-K", "la pampa": "AR-L", "mendoza": "AR-M", "misiones": "AR-N",
    "formosa": "AR-P", "neuquen": "AR-Q", "rio negro": "AR-R", "santa fe": "AR-S",
    "tucuman": "AR-T", "chubut": "AR-U", "tierra del fuego": "AR-V", "corrientes": "AR-W",
    "cordoba": "AR-X", "jujuy": "AR-Y", "santa cruz": "AR-Z",
}


def _plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split())


def region_code(locality: str, region: str) -> str | None:
    """Livepass writes the region inconsistently ("Buenos Aires" for both the city and the
    province), so the city is recognised by its "Comuna N" locality or its explicit name."""
    place, area = _plain(locality), _plain(region)
    if _COMUNA.match(place) or "ciudad autonoma" in area or area == "capital federal":
        return "AR-C"
    if area.startswith("provincia de "):
        area = area[len("provincia de "):]
    return _PROVINCES.get(area)


def event_paths_from_listing(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    paths = {a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("/events/")}
    return sorted(paths)


def _event_jsonld(html: str) -> dict | None:
    for script in BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type") == "Event":
                return item
    return None


def parse_event(html: str, now: datetime) -> Event | None:
    data = _event_jsonld(html)
    if not data or not data.get("name") or not data.get("startDate") or not data.get("url"):
        return None
    starts_at = datetime.fromisoformat(data["startDate"])
    if starts_at.tzinfo is None:  # some events omit the offset; Livepass sells Argentine shows
        starts_at = starts_at.replace(tzinfo=BA)
    if starts_at < now:
        return None
    place = data.get("location") or {}
    address = place.get("address") or {}
    offers = data.get("offers") or {}
    slug = urlparse(data["url"]).path.rstrip("/").rsplit("/", 1)[-1]
    region = region_code(address.get("addressLocality") or "", address.get("addressRegion") or "")
    # For the city, Livepass gives the comuna ("Comuna 14") instead of a city name.
    city = "Buenos Aires" if region == "AR-C" else address.get("addressLocality")
    return Event(
        id=f"livepass-{slug}-{starts_at:%Y%m%dT%H%M}",
        category="concert",  # everything under /t/show
        title=data["name"],
        venue=place.get("name") or "",
        city=city,
        region=region,
        country=address.get("addressCountry"),
        starts_at=starts_at,
        ticket_links=[TicketLink(vendor=VENDOR, url=offers.get("url") or data["url"])],
        source_url=data["url"],
        updated_at=now,
    )


def filter_regions(events: list[Event], regions: frozenset[str] | None) -> list[Event]:
    return events if regions is None else [e for e in events if e.region in regions]


def scrape(regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0) -> list[Event]:
    """Fetch the listing and every event page, pausing `delay` seconds between requests."""
    now = datetime.now(tz=BA)
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, follow_redirects=True) as client:
        listing = client.get(BASE_URL + LISTING_PATH).raise_for_status().text
        for path in event_paths_from_listing(listing):
            time.sleep(delay)
            response = client.get(BASE_URL + path)
            if response.status_code != 200:
                continue
            event = parse_event(response.text, now)
            if event:
                events.append(event)
    return filter_regions(events, regions)
