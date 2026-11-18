"""Scraper for Enigma Tickets, from the data its own pages render (a Remix app).

Findings on 2026-11-17. Every page carries its data in `window.__remixContext` (loader data):
- the home lists `featuredEvents` and `nextEvents` (22 cards: 21 shows and one tour);
- the search (/search/event, no text) lists every show 21 at a time: page 1 is rendered, later
  pages are what the site's own script asks for, a POST to the same route with `page` and
  `pageSize`. It held the same 22 cards as the home. The 63 venue pages (/<venue>) together held
  20 of them: not the tour, and not a show whose venue shares its link with another venue;
- a tour (/tour/<uuid>) is not a show: it lists its shows, which are also in the search.
Each show's page (/event/<uuid>) holds one schedule per date, with the day as numbers and the time
only in its labels ("Lun 30/11 20:30hs", "26 de Noviembre 21:00hs"); a festival can keep a
placeholder day and write the real ones in the label ("16, 17 y 18 DE ABRIL"). Passes ("Abonos")
have no date. The site gives no category, and the venue has no address: only a Google Maps short
link, whose redirect carries the place's coordinates (read from the Location header, not
followed). An unknown show answers 500. robots.txt is a 404 page: no rules.
"""

import json
import re
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import city_name, plain, region_code
from app.scrapers.georef import province_at
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://www.enigmatickets.com"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Enigma Tickets"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
SEARCH_PAGE_SIZE = 21  # what the site's own script asks for
MAX_SEARCH_PAGES = 20
MAX_SHOW_PAGES = 300  # 21 shows on 2026-11-17

_CONTEXT = re.compile(r"window\.__remixContext\s*=\s*")
_CLOCK = re.compile(r"\b(\d{1,2}):(\d{2})\s*hs\b")
_DAYS = re.compile(r"^(\d{1,2}(?:\s*(?:,|y)\s*\d{1,2})*)\s+de\s+([a-z]+)\b")
_PLACE_PIN = re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)")
_MONTHS = {name: number for number, name in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}


class ListingTooLongError(RuntimeError):
    """More pages than expected: stop rather than store part of them."""


def _loader_data(page: str) -> dict:
    match = _CONTEXT.search(page)
    if not match:
        return {}
    try:
        context = json.JSONDecoder().raw_decode(page, match.end())[0]
    except ValueError:
        return {}
    data = ((context or {}).get("state") or {}).get("loaderData")
    return data if isinstance(data, dict) else {}


def _split(cards: list) -> tuple[set[str], set[str]]:
    shows, tours = set(), set()
    for card in cards:
        if isinstance(card, dict) and isinstance(card.get("uid"), str):
            (tours if card.get("isTour") else shows).add(card["uid"])
    return shows, tours


def _cards(page: str) -> list:
    cards = []
    for route in _loader_data(page).values():
        if isinstance(route, dict):
            for key in ("featuredEvents", "nextEvents", "initialEvents", "childEvents"):
                cards += route.get(key) or []
    return cards


def listed(page: str) -> tuple[set[str], set[str]]:
    """The shows and the tours a home, search or tour page lists, by uuid."""
    return _split(_cards(page))


def event_data(page: str) -> dict | None:
    """The show on its page; None when the page holds no show."""
    route = _loader_data(page).get("routes/event.$eventId")
    event = route.get("event") if isinstance(route, dict) else None
    return event if isinstance(event, dict) and event.get("uid") else None


def venue_point(location: str | None) -> tuple[float, float] | None:
    """The place's own pin in a Google Maps URL ("!3d<lat>!4d<lon>"), not the view's centre after "@"."""
    match = _PLACE_PIN.search(location or "")
    return (float(match[1]), float(match[2])) if match else None


def region_of(province: str | None) -> str | None:
    """ISO region from Georef's province name."""
    return region_code("", province) if province else None


def _days(schedule: dict) -> list[date]:
    """The days a schedule stands for: the ones its label lists, else its own."""
    day = schedule.get("date")
    if not isinstance(day, dict):
        return []  # a pass
    listed_days = _DAYS.match(plain(schedule.get("labelForReplaceDate") or ""))
    if listed_days and listed_days[2] in _MONTHS:
        month = _MONTHS[listed_days[2]]
        return [date(day["year"], month, int(n)) for n in re.findall(r"\d+", listed_days[1])]
    return [date(day["year"], day["month"], day["day"])]


def _clock(schedule: dict) -> tuple[int, int] | None:
    for text in (schedule.get("labelForReplaceDate"), schedule.get("title")):
        match = _CLOCK.search(text or "")
        if match:
            return int(match[1]), int(match[2])
    return None


def parse_event(
    data: dict | None, *, province: str | None, now: datetime, point: tuple[float, float] | None = None
) -> list[Event]:
    """One event per date of the show that has not passed yet. `province` is Georef's name for where
    the venue is, if known."""
    if not data:
        return []
    title, venue = clean_text(data.get("title") or ""), clean_text((data.get("venue") or {}).get("name") or "")
    if not title or not venue:
        return []
    region = region_of(province)
    url = f"{SITE}/event/{data['uid']}"
    events = []
    for schedule in (data.get("schedules") or {}).values():
        if not isinstance(schedule, dict):
            continue
        clock = _clock(schedule)
        for day in _days(schedule):
            starts_at = datetime(day.year, day.month, day.day, *(clock or (0, 0)), tzinfo=BA)
            if (starts_at < now) if clock else (day < now.date()):
                continue
            events.append(Event(
                id=f"enigma-{data['uid']}-{starts_at:%Y%m%dT%H%M}",
                category=provisional_category(title, starts_at),
                title=title,
                venue=venue,
                city=city_name(None, region),
                region=region,
                country="AR",
                starts_at=starts_at,
                time_known=clock is not None,
                ticket_links=[TicketLink(vendor=VENDOR, url=url)],
                source_url=url,
                **source_image(data.get("imageUrl")),
                venue_point=point,
                updated_at=now,
            ))
    return events


def _map_redirect(client: httpx.Client, link: str | None) -> str | None:
    if not link or not link.startswith("https://maps.app.goo.gl/"):
        return link
    try:
        return client.get(link, follow_redirects=False).headers.get("location")
    except httpx.HTTPError:
        return None


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Read the home, every search page and each tour, then each show, pausing `delay` seconds
    between requests. A listing page that fails stops the scrape (the runner reports it); a show
    that fails is skipped."""
    now = datetime.now(tz=BA)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:

        def get(path: str) -> str:
            text = client.get(SITE + path).raise_for_status().text
            time.sleep(delay)
            return text

        shows, tours = listed(get("/"))
        found = listed(get("/search/event"))
        shows, tours = shows | found[0], tours | found[1]
        size, number = len(found[0]) + len(found[1]), 1
        while size == SEARCH_PAGE_SIZE:
            number += 1
            if number > MAX_SEARCH_PAGES:
                raise ListingTooLongError(f"more than {MAX_SEARCH_PAGES} search pages; raise MAX_SEARCH_PAGES")
            response = client.post(
                f"{SITE}/search/event", params={"_data": "routes/search.event"},
                data={"page": number, "pageSize": SEARCH_PAGE_SIZE},
            ).raise_for_status()
            time.sleep(delay)
            cards = response.json()
            more = _split(cards)
            shows, tours, size = shows | more[0], tours | more[1], len(cards)
        for tour in sorted(tours):
            shows |= listed(get(f"/tour/{tour}"))[0]

        if len(shows) > MAX_SHOW_PAGES:
            raise ListingTooLongError(f"more than {MAX_SHOW_PAGES} show pages; raise MAX_SHOW_PAGES")
        provinces: dict[str, str | None] = {}
        points: dict[str, tuple[float, float] | None] = {}
        events: list[Event] = []
        for uid in sorted(shows):
            response = client.get(f"{SITE}/event/{uid}")
            time.sleep(delay)
            data = event_data(response.text) if response.status_code == 200 else None
            if data is None:
                continue
            venue = data.get("venue") or {}
            key = venue.get("uid") or venue.get("name") or ""
            if key not in provinces:
                location = _map_redirect(client, venue.get("url"))
                time.sleep(delay)
                point = points[key] = venue_point(location)
                provinces[key] = province_at(client, point) if point else None
            events += parse_event(data, province=provinces[key], now=now, point=points[key])
    return events if regions is None else [e for e in events if e.region in regions]
