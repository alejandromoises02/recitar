"""Scraper for the Teatro Colon monthly calendar (server-rendered HTML, no API)."""

import logging
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.images import first_image_url, source_image
from app.scrapers.text import clean_text

BA = ZoneInfo("America/Argentina/Buenos_Aires")
VENUE = "Teatro Colón"
# The Colón sells most performances on the city's Entradas BA, but some go through a ticketer;
# the vendor is read from the link's domain, and an unknown domain is shown as it is.
TICKET_VENDORS = {
    "entradasba.buenosaires.gob.ar": "Entradas BA",
    "tuentrada.com": "TuEntrada",
    "ticketek.com.ar": "Ticketek",
}
CALENDAR_URL = "https://teatrocolon.org.ar/calendario/?a={year}&mes={month}"
USER_AGENT = "recitAR-research/0.1"

_HOUR = re.compile(r"(\d{1,2})\.(\d{2})")
_DAY = re.compile(r"\d{1,2}")

# The site's own program labels, as seen from November 2026 to January 2027. A label not listed
# falls back to "other" and is logged, so a new one is noticed. Children's shows are theatre, as
# family shows are in the other sources; CETC (the experimental centre) and the season's guided
# visits and documentary screenings are "other".
_CATEGORIES: dict[str, EventCategory] = {
    "Ópera": "theatre",
    "Ballet": "theatre",
    "Colón para niños": "theatre",
    "Filarmónica de Buenos Aires": "concert",
    "Música de Cámara": "concert",
    "Clásica Joven": "concert",
    "Corales": "concert",
    "Conciertos extraordinarios": "concert",
    "Salón Dorado": "concert",
    "Fuera de Ciclo": "concert",
    "Grandes Intérpretes": "concert",
    "Contemporáneo": "concert",
    "Orquesta Académica del Teatro Colón": "concert",
    "CETC": "other",
    "Temporada 2026": "other",
    "Cine Documental": "other",
}
_log = logging.getLogger(__name__)


def _category(label: str | None, unknown: set[str]) -> EventCategory:
    if label is not None and label not in _CATEGORIES:
        unknown.add(label)
    return _CATEGORIES.get(label or "", "other")


def parse_calendar(html: str, year: int, month: int, now: datetime) -> list[Event]:
    """Events of one calendar page. The page shows only day and hour, so the caller gives year/month."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[Event] = []
    unknown: set[str] = set()
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
                category=_category(category.get_text(strip=True) if category else None, unknown),
                title=clean_text(title.get_text(" ", strip=True)),
                venue=VENUE,
                city="Buenos Aires",
                region="AR-C",
                country="AR",
                starts_at=starts_at,
                ticket_links=[TicketLink(vendor=ticket_vendor(buy["href"]), url=buy["href"])] if buy else [],
                source_url=info["href"],
                **source_image(first_image_url(picture.get("src") if picture else None)),
                updated_at=now,
            )
        )
    for label in sorted(unknown):
        _log.warning('Teatro Colón program label not mapped: "%s"', label)
    return events


def ticket_vendor(url: str) -> str:
    """Who sells a ticket link, from its domain."""
    host = (urlparse(url).hostname or "").removeprefix("www.")
    return TICKET_VENDORS.get(host, host)


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
