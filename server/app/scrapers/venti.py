"""Scraper for Venti: the public sitemap, then each event page's schema.org JSON-LD.

robots.txt asks for a 10 second crawl delay, which this module never goes below.
"""

import json
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import city_name, plain, region_code

SITEMAP_URL = "https://venti.live/sitemap.xml"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Venti"
CRAWL_DELAY = 10.0
BA = ZoneInfo("America/Argentina/Buenos_Aires")


def event_urls_from_sitemap(xml: str, hint: str | None) -> list[str]:
    """Event page URLs; `hint` keeps only those whose slug contains it (a cheap pre-filter)."""
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    events = [u for u in urls if urlparse(u).path.startswith("/evento/")]
    return events if hint is None else [u for u in events if plain(hint) in plain(u)]


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
    starts_at = starts_at.replace(tzinfo=BA) if starts_at.tzinfo is None else starts_at.astimezone(BA)
    if starts_at < now:
        return None
    place = data.get("location") or {}
    address = place.get("address") or {}
    offers = data.get("offers") or {}
    slug = urlparse(data["url"]).path.rstrip("/").rsplit("/", 1)[-1]
    region = region_code(address.get("addressLocality") or "", address.get("addressRegion") or "")
    return Event(
        id=f"venti-{slug}-{starts_at:%Y%m%dT%H%M}",
        category=provisional_category(data["name"], starts_at),
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


def filter_venue(events: list[Event], venue: str | None) -> list[Event]:
    """Keep events whose venue name contains `venue` (accent and case insensitive)."""
    return events if venue is None else [e for e in events if plain(venue) in plain(e.venue)]


def scrape(venue: str | None = "niceto", delay: float = CRAWL_DELAY) -> list[Event]:
    """Fetch the sitemap and every candidate event page, pausing at least the crawl delay."""
    delay = max(delay, CRAWL_DELAY)
    now = datetime.now(tz=BA)
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, follow_redirects=True) as client:
        sitemap = client.get(SITEMAP_URL).raise_for_status().text
        for url in event_urls_from_sitemap(sitemap, venue):
            time.sleep(delay)
            response = client.get(url)
            if response.status_code != 200:
                continue
            event = parse_event(response.text, now)
            if event:
                events.append(event)
    return filter_venue(events, venue)
