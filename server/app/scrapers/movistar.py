"""Scraper for Movistar Arena: facts only (title, date, place, official link).

The site is a Blazor app: the page is built in the browser over a WebSocket, so the listing
and each show page are rendered with Playwright. Each show page carries schema.org JSON-LD
with one MusicEvent per date. Images and descriptions are deliberately not read: its terms
forbid reproducing its content, so its events get images from the alternative plan instead.
"""

import json
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import city_name, region_code
from app.scrapers.text import clean_text

BASE_URL = "https://www.movistararena.com.ar"
LISTING_PATH = "/shows"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Movistar Arena"
BA = ZoneInfo("America/Argentina/Buenos_Aires")

_JSON_LD = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def shows_from_listing(html: str) -> list[str]:
    """Show page paths (/show/<id>), one per show. The listing only shows the first date."""
    soup = BeautifulSoup(html, "html.parser")
    paths = [a["href"] for a in soup.select('div.evento a.mas-info[href^="/show/"]')]
    return list(dict.fromkeys(paths))


def _event_items(html: str) -> list[dict]:
    items: list[dict] = []
    for block in _JSON_LD.findall(html):
        # Blazor puts an HTML comment before the JSON; a single date is an object, several a list.
        try:
            data = json.loads(_HTML_COMMENT.sub("", block))
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            kind = item.get("@type") if isinstance(item, dict) else None
            kinds = kind if isinstance(kind, list) else [kind]
            if any(isinstance(k, str) and k.endswith("Event") for k in kinds):
                items.append(item)
    return items


def parse_show(html: str, now: datetime) -> list[Event]:
    events: dict[str, Event] = {}
    for item in _event_items(html):
        if not (item.get("name") and item.get("startDate") and item.get("url")):
            continue
        starts_at = datetime.fromisoformat(item["startDate"])
        starts_at = starts_at.replace(tzinfo=BA) if starts_at.tzinfo is None else starts_at.astimezone(BA)
        if starts_at < now:
            continue
        place = item.get("location") or {}
        address = place.get("address") or {}
        region = region_code(address.get("addressLocality") or "", address.get("addressRegion") or "")
        show_id = urlparse(item["url"]).path.rstrip("/").rsplit("/", 1)[-1]
        event = Event(
            id=f"movistar-{show_id}-{starts_at:%Y%m%dT%H%M}",
            category=provisional_category(clean_text(item["name"]), starts_at),
            title=clean_text(item["name"]),
            venue=place.get("name") or "",
            city=city_name(address.get("addressLocality"), region),
            region=region,
            country=address.get("addressCountry"),
            starts_at=starts_at,
            ticket_links=[TicketLink(vendor=VENDOR, url=(item.get("offers") or {}).get("url") or item["url"])],
            source_url=item["url"],
            updated_at=now,
        )
        events[event.id] = event
    return list(events.values())


def _render(page, url: str, settle: float = 3.0) -> str:
    page.goto(url, wait_until="networkidle", timeout=60_000)
    time.sleep(settle)  # Blazor keeps filling the page after the network goes quiet
    return page.content()


def scrape(delay: float = 5.0, limit: int | None = None) -> list[Event]:
    """Render the listing and every show page in a headless browser, pausing `delay` seconds between pages."""
    from playwright.sync_api import sync_playwright

    now = datetime.now(tz=BA)
    events: list[Event] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(user_agent=USER_AGENT, locale="es-AR", timezone_id="America/Argentina/Buenos_Aires")
        page = context.new_page()
        try:
            for path in shows_from_listing(_render(page, BASE_URL + LISTING_PATH))[:limit]:
                time.sleep(delay)
                events.extend(parse_show(_render(page, BASE_URL + path), now))
        finally:
            browser.close()
    return events
