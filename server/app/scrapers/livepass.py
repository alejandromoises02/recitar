"""Scraper for Livepass: the public /t/show listing, then each event's schema.org JSON-LD."""

import json
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.domain.event import Event, TicketLink
from app.scrapers.geo import city_name, region_code

BASE_URL = "https://www.livepass.com.ar"
LISTING_PATH = "/t/show"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Livepass"
BA = ZoneInfo("America/Argentina/Buenos_Aires")

# Where to show events. The scraper stores every region; this is only the default filter.
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})


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
    return Event(
        id=f"livepass-{slug}-{starts_at:%Y%m%dT%H%M}",
        category="concert",  # everything under /t/show
        title=data["name"],
        venue=place.get("name") or "",
        city=city_name(address.get("addressLocality"), region),
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
