"""Scraper for Articket, a Mar del Plata ticketer, from the pages its own site renders.

What the site showed on 2026-11-17:
- listings are the home with a query: `?buscar=<text>` searches, `?categoria=<name>` filters. Each
  show is a card (`<div id="caja-N">`) with its title, first date, image and "venue, city, province".
  A listing holds every card: "Ver más" only unhides cards already in the page. An empty search gives
  the home (8 curated shows, no cards), so the listing is one search per vowel: together they gave 68
  shows, the same 68 as a search for a space, and every show of every category was among them;
- the category is only a filter, so each category is listed too and a show takes the ones it was under.
  On that day 58 shows were under exactly one category and 10 under none. The city/venue
  subcategories (`?subcategoria=`) listed nothing;
- a show's page (/<SLUG>/) lists its performances in a <select> ("04-12-2026, 21:30", or
  "09 01 2027, 21:00hs" when there are several, after a "Seleccione una Fecha" placeholder). Its
  schema.org Event has only the first date and is not always valid JSON. It gives the address as
  "street city, province" glued together and no coordinates, so the location comes from the card.
  A slug that is not a show redirects home (301);
- cards spell a city several ways ("Mar del Plata", "MAR DEL PLATA", "Mar del plata").
robots.txt holds only Cloudflare's content-signal comments, no rules.
"""

import html
import re
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from app.domain.event import Event, EventCategory, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import city_name, plain, region_code
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://articket.com.ar"
USER_AGENT = "recitAR-research/0.1"
VENDOR = "Articket"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
SEARCHES = "aeiou"
MAX_SHOW_PAGES = 300  # 68 shows on 2026-11-17

# Articket's categories, as its filter takes them. Children's shows are stage shows, so theatre.
# Sports are not shows. Anything else (cinema, conventions, parks, holistic events), or no category, is "other".
CATEGORIES: dict[str, EventCategory | None] = {
    "Recitales": "concert", "Teatros": "theatre", "Infantiles": "theatre", "Fiestas": "other",
    "Deporte": None, "Cine": "other", "Convención": "other", "Evento Holisitico": "other", "Parques": "other",
}

_CARD = re.compile(r'<div id="caja-\d+"')
_TITLE = re.compile(r'<h4 class="card-title"[^>]*>([^<]*)</h4>')
_PLACE = re.compile(r'class="card-text address" alt="([^"]*)"')
_IMAGE = re.compile(r'<img [^>]*src="([^"]+)"')
_LINK = re.compile(r'<a href="\s*/([^/"\s]+)/?\s*"')
_DATES = re.compile(r'<select[^>]*id="idFechasEventos"[^>]*>(.*?)</select>', re.S)
_OPTION = re.compile(r'<option[^>]*value="\d+"[^>]*>([^<]*)</option>')
_DATE = re.compile(r"(\d{1,2})[-/ ](\d{1,2})[-/ ](\d{4})(?:,\s*(\d{1,2}):(\d{2}))?")
_OG_IMAGE = re.compile(r'<meta property="og:image" content="([^"]+)"')


class ListingTooLongError(RuntimeError):
    """More show pages than expected: stop rather than store part of them."""


@dataclass(frozen=True)
class Card:
    slug: str
    title: str
    venue: str
    city: str | None
    province: str | None
    image: str | None


def _absolute(src: str | None) -> str | None:
    if not src:
        return None
    return src if src.startswith(("http://", "https://")) else SITE + "/" + src.lstrip("/")


def cards(page: str) -> list[Card]:
    """The shows a listing page links to, as their cards describe them."""
    found = []
    for chunk in _CARD.split(page)[1:]:
        link, title = _LINK.search(chunk), _TITLE.search(chunk)
        if not link or not title:
            continue
        place = _PLACE.search(chunk)
        parts = [clean_text(p) for p in html.unescape(place.group(1)).rsplit(",", 2)] if place else []
        venue, city, province = (parts + ["", "", ""])[:3] if len(parts) == 3 else ((parts or [""])[0], "", "")
        image = _IMAGE.search(chunk)
        found.append(Card(
            slug=link.group(1), title=clean_text(html.unescape(title.group(1))), venue=venue,
            city=city or None, province=province or None, image=_absolute(image and html.unescape(image.group(1))),
        ))
    return found


def city_spellings(found: Iterable[Card]) -> dict[str, str]:
    """For each city, its most common spelling on the cards, preferring one not in capitals."""
    counts: dict[str, Counter[str]] = {}
    for card in found:
        if card.city:
            counts.setdefault(plain(card.city), Counter())[card.city] += 1
    return {
        key: max(spellings, key=lambda s: (not s.isupper(), spellings[s]))
        for key, spellings in counts.items()
    }


def performances(page: str) -> list[tuple[datetime, bool]]:
    """Each date in the show page's date picker, in Buenos Aires time, and whether it has a time."""
    picker = _DATES.search(page)
    found = []
    for option in _OPTION.findall(picker.group(1)) if picker else []:
        match = _DATE.search(option)
        if not match:
            continue
        day, month, year, hour, minute = match.groups()
        found.append((
            datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), tzinfo=BA),
            hour is not None,
        ))
    return found


def show_image(page: str) -> str | None:
    match = _OG_IMAGE.search(page)
    return _absolute(html.unescape(match.group(1))) if match else None


def category_of(listed_under: set[str], title: str, starts_at: datetime) -> EventCategory | None:
    kinds = {CATEGORIES.get(name, "other") for name in listed_under} or {"other"}
    if None in kinds:
        return None
    if "concert" in kinds:
        return provisional_category(title, starts_at)
    return "theatre" if "theatre" in kinds else "other"


def parse_show(page: str, card: Card, *, listed_under: set[str], city: str | None, now: datetime) -> list[Event]:
    """One event per performance of the card's show that has not started yet. `city` is the card's
    city as it is usually spelled."""
    if not card.title or not card.venue:
        return []
    region = region_code(card.city or "", card.province or "")
    url = f"{SITE}/{card.slug}/"
    image = show_image(page) or card.image
    events = []
    for starts_at, time_known in performances(page):
        if starts_at < now:
            continue
        category = category_of(listed_under, card.title, starts_at)
        if category is None:
            continue
        events.append(Event(
            id=f"articket-{card.slug.lower()}-{starts_at:%Y%m%dT%H%M}",
            category=category,
            title=card.title,
            venue=card.venue,
            city=city_name(city, region),
            region=region,
            country="AR",
            starts_at=starts_at,
            time_known=time_known,
            ticket_links=[TicketLink(vendor=VENDOR, url=url)],
            source_url=url,
            **source_image(image),
            updated_at=now,
        ))
    return events


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES, delay: float = 2.0, transport: httpx.BaseTransport | None = None
) -> list[Event]:
    """Search each vowel, list each category, then read each show's page, pausing `delay` seconds
    between requests. A listing page that fails stops the scrape (the runner reports it); a show
    that fails is skipped."""
    now = datetime.now(tz=BA)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:

        def listing(params: dict[str, str]) -> list[Card]:
            found = cards(client.get(SITE + "/", params=params).raise_for_status().text)
            time.sleep(delay)
            return found

        shows: dict[str, Card] = {}
        for vowel in SEARCHES:
            for card in listing({"buscar": vowel}):
                shows.setdefault(card.slug, card)
        listed_under: dict[str, set[str]] = {}
        for category in CATEGORIES:
            for card in listing({"categoria": category}):
                shows.setdefault(card.slug, card)
                listed_under.setdefault(card.slug, set()).add(category)
        if len(shows) > MAX_SHOW_PAGES:
            raise ListingTooLongError(f"{len(shows)} shows, more than {MAX_SHOW_PAGES}; raise MAX_SHOW_PAGES")
        spellings = city_spellings(shows.values())
        events: list[Event] = []
        for slug, card in shows.items():
            try:
                response = client.get(f"{SITE}/{quote(slug, safe='')}/")  # a gone show redirects home: not followed
            except httpx.HTTPError:
                response = None
            time.sleep(delay)
            if response is None or response.status_code != 200:
                continue
            city = spellings.get(plain(card.city)) if card.city else None
            events += parse_show(response.text, card, listed_under=listed_under.get(slug, set()), city=city, now=now)
    return events if regions is None else [e for e in events if e.region in regions]
