"""Scraper for the Teatro Colon monthly calendar (server-rendered HTML, no API)."""

import re
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.images import first_image_url, source_image

BA = ZoneInfo("America/Argentina/Buenos_Aires")
VENUE = "Teatro Colón"
TICKET_VENDOR = "Entradas BA"
CALENDAR_URL = "https://teatrocolon.org.ar/calendario/?a={year}&mes={month}"
USER_AGENT = "recitAR-research/0.1"

_HOUR = re.compile(r"(\d{1,2})\.(\d{2})")
_DAY = re.compile(r"\d{1,2}")

# The site's own program labels. Anything not listed falls back to "other".
_CATEGORIES: dict[str, EventCategory] = {
    "Ópera": "theatre",
    "Ballet": "theatre",
    "Filarmónica de Buenos Aires": "concert",
    "Música de Cámara": "concert",
    "Clásica Joven": "concert",
    "Corales": "concert",
    "Conciertos extraordinarios": "concert",
    "Salón Dorado": "concert",
}


def parse_calendar(html: str, year: int, month: int, now: datetime) -> list[Event]:
    """Events of one calendar page. The page shows only day and hour, so the caller gives year/month."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[Event] = []
    for item in soup.select("div.calendar-item"):
        day = item.select_one(".day-number")
        hour = item.select_one(".day-hour")
        title = item.select_one("h1")
        info = item.select_one(".buttons a.grey")
        if not (day and hour and title and info):
            continue
        day_match, hour_match = _DAY.search(day.get_text()), _HOUR.search(hour.get_text())
        if not (day_match and hour_match):
            continue
        starts_at = datetime(year, month, int(day_match.group()), int(hour_match[1]), int(hour_match[2]), tzinfo=BA)
        if starts_at < now:
            continue
        category = item.select_one(".category")
        buy = item.select_one(".buttons a:not(.grey)")
        picture = item.find("img")
        slug = urlparse(info["href"]).path.rstrip("/").rsplit("/", 1)[-1]
        events.append(
            Event(
                id=f"colon-{slug}-{starts_at:%Y%m%dT%H%M}",
                category=_CATEGORIES.get(category.get_text(strip=True), "other") if category else "other",
                title=" ".join(title.get_text(" ", strip=True).split()),
                venue=VENUE,
                city="Buenos Aires",
                region="AR-C",
                country="AR",
                starts_at=starts_at,
                ticket_links=[TicketLink(vendor=TICKET_VENDOR, url=buy["href"])] if buy else [],
                source_url=info["href"],
                **source_image(first_image_url(picture.get("src") if picture else None)),
                updated_at=now,
            )
        )
    return events


def scrape(months: int = 3, delay: float = 2.0) -> list[Event]:
    """Fetch the calendar for this month and the next ones, pausing `delay` seconds between requests."""
    now = datetime.now(tz=BA)
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True) as client:
        for offset in range(months):
            index = now.month - 1 + offset
            year, month = now.year + index // 12, index % 12 + 1
            if offset:
                time.sleep(delay)
            response = client.get(CALENDAR_URL.format(year=year, month=month))
            response.raise_for_status()
            events.extend(parse_calendar(response.text, year, month, now))
    return events
