"""Parser for Teatro Colon production pages (server-rendered HTML, no API)."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.domain.event import Event, TicketLink

BA = ZoneInfo("America/Argentina/Buenos_Aires")
VENUE = "Teatro Colón"
TICKET_VENDOR = "Entradas BA"
_DATE = re.compile(r"(\d{1,2})/(\d{1,2}),\s*(\d{1,2}):(\d{2})")
_SEASON = re.compile(r"season-temporada-(\d{4})")
_DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def parse_production(html: str, source_url: str, now: datetime) -> list[Event]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1").get_text(strip=True)
    slug = source_url.rstrip("/").rsplit("/", 1)[-1]
    season_year = _season_year(soup, now)

    events: list[Event] = []
    for day in soup.select("div.day"):
        mobile = day.select_one("span.hide-desktop p")
        link = day.find("a", href=True)
        match = _DATE.search(mobile.get_text(" ", strip=True)) if mobile else None
        if not match or not link:
            continue
        weekday = mobile.select_one("span.capitalize").get_text(strip=True).lower()
        d, m, hh, mm = (int(g) for g in match.groups())
        starts_at = _resolve_year(season_year, m, d, hh, mm, weekday)
        if starts_at is None:
            continue
        events.append(
            Event(
                id=f"colon-{slug}-{starts_at:%Y%m%dT%H%M}",
                category="other",
                artist=title,
                venue=VENUE,
                starts_at=starts_at,
                ticket_links=[TicketLink(vendor=TICKET_VENDOR, url=link["href"])],
                source_url=source_url,
                updated_at=now,
            )
        )
    return events


def _season_year(soup: BeautifulSoup, now: datetime) -> int:
    for tag in soup.find_all(class_=True):
        found = _SEASON.search(" ".join(tag["class"]))
        if found:
            return int(found.group(1))
    return now.year


def _resolve_year(season_year: int, month: int, day: int, hour: int, minute: int, weekday: str):
    """The page omits the year: pick the one near the season whose weekday matches."""
    for year in (season_year, season_year + 1, season_year - 1):
        try:
            candidate = datetime(year, month, day, hour, minute, tzinfo=BA)
        except ValueError:
            continue
        if _DAY_NAMES[candidate.weekday()] == weekday:
            return candidate
    return None
