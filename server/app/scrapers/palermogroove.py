"""Scraper for Palermo Groove (palermogroove.com.ar), from the listing on its own home page.

The venue sells through Passline, whose site answers 403 (a Cloudflare challenge) to every request
without a browser; the venue's site does not. What 2026-11-25 showed:
- the home (a WordPress page) lists every show as `<a class="pl-link" href="<passline event>">`
  around an `<img src="<flyer>" alt="<text>">`: 26 shows, and no page of its own for any of them;
- the alt text is the show's title, typed by hand, with the date in it for 14 of them and in no
  fixed format ("@ 27.11.2026", "28/11", "@ Domingo 29 de noviembre de 2026", "27..12.2026",
  "/ 19.2 /"); one carries a year already past ("CAIBO en Groove @ 21.02.2026");
- no show gives a time; the flyers (400 px JPEGs on imagenes.passline.com, which answers without
  the challenge) print the date as "LUNES 24 DE MAYO 2027" or "10 DE DICIEMBRE".
robots.txt only disallows /wp-admin/. Every show is at the venue (Av. Santa Fe 4389, City of Buenos Aires).

A show whose text gives no usable date gets it from its flyer by OCR (Tesseract, run as a program),
and only when the reading is unambiguous: one "day DE month" in the text, a real future day, and the
weekday matching when one is printed, and six passes (colour and grey, three page modes) agreeing:
at least two read it and none reads another day. Otherwise it is left out and logged: a wrong date
would send people to the venue on the wrong night. On 4 real flyers (2026-11-25): 2 read 6 of 6
passes alike; 1 was read as the 10th by one pass and the 19th by another, so it is left out; 1 is
not read at all (boxed letters).
"""

import logging
import re
import shutil
import subprocess
import time
from datetime import date, datetime, timedelta
from html import unescape
from io import BytesIO
from zoneinfo import ZoneInfo

import httpx
from PIL import Image, ImageOps

from app.domain.event import Event, TicketLink
from app.scrapers.category import provisional_category
from app.scrapers.geo import CITY_OF_BUENOS_AIRES, city_name, plain
from app.scrapers.images import source_image
from app.scrapers.text import clean_text

SITE = "https://www.palermogroove.com.ar/"
USER_AGENT = "recitAR-research/0.1"
VENUE = "Palermo Groove"
VENDOR = "Passline"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = frozenset({"AR-C", "AR-B"})
MAX_SHOWS = 150  # 26 shows on 2026-11-25
MAX_AHEAD = timedelta(days=550)  # a date further away than this is a misreading
OCR_SCALE = 3  # the flyers are 400 px: Tesseract misses digits at that size
OCR_TIMEOUT = 60
OCR_PAGE_MODES = ("3", "6", "11")  # whole page, one block, scattered text
MIN_AGREEING = 2

_log = logging.getLogger(__name__)

_CARD = re.compile(r'<a class="pl-link" href="([^"]+)".*?<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', re.S)
_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_WEEKDAYS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
_MONTH = "|".join(_MONTHS)
_WEEKDAY = "|".join(_WEEKDAYS)
# "Domingo 29 de noviembre de 2026", "LUNES 24 DE MAYO 2027", "10 DE DICIEMBRE"; matched on plain text.
_WORDS_DATE = re.compile(
    rf"(?:\b({_WEEKDAY})\s+)?\b(\d{{1,2}})\s+de\s+({_MONTH})\b(?:\s+(?:de\s+)?(\d{{4}})\b)?"
)
# "27.11.2026", "27..12.2026", "28/11", "19.2": typed by hand in the alt text only.
_NUMBERS_DATE = re.compile(r"(?<![\d.])(\d{1,2})(?:\.{1,2}|/)(\d{1,2})(?:(?:\.{1,2}|/)(\d{4}))?(?![\d.])")
# The date as it sits in the alt text, with what introduces it, for removing it from the title.
_ALT_DATE_TEXT = re.compile(
    rf"\s*@?\s*(?:(?:{_WEEKDAY})\s+)?(?:\d{{1,2}}\s+de\s+(?:{_MONTH})(?:\s+(?:de\s+)?\d{{4}})?"
    r"|(?<![\d.])\d{1,2}(?:\.{1,2}|/)\d{1,2}(?:(?:\.{1,2}|/)\d{4})?(?![\d.]))",
    re.I,
)


class ListingTooLongError(RuntimeError):
    """More shows than expected: stop rather than store part of them."""


def cards(page: str) -> list[tuple[str, str, str]]:
    """(Passline link, flyer URL, alt text) of each show on the home, in order, once each."""
    seen: dict[str, tuple[str, str, str]] = {}
    for link, image, alt in _CARD.findall(page):
        seen.setdefault(link, (link, image, clean_text(unescape(alt))))
    return list(seen.values())


def _resolve(day: int, month: int, year: int | None, today: date) -> date | None:
    """The day meant, or None if it does not exist, has passed or is implausibly far away. With
    no year, the next time that day comes."""
    try:
        when = date(year or today.year, month, day)
        if year is None and when < today:
            when = date(today.year + 1, month, day)
    except ValueError:
        return None
    return when if today <= when <= today + MAX_AHEAD else None


def _one(found: set[date | None]) -> date | None:
    """A single readable date, or None: two different dates, or one that did not resolve, are not trusted."""
    return found.pop() if len(found) == 1 else None


def _words_dates(text: str, today: date) -> set[date | None]:
    found: set[date | None] = set()
    for weekday, day, month, year in _WORDS_DATE.findall(plain(text)):
        when = _resolve(int(day), _MONTHS[month], int(year) if year else None, today)
        if when is not None and weekday and when.weekday() != _WEEKDAYS[weekday]:
            when = None
        found.add(when)
    return found


def alt_date(alt: str, today: date) -> date | None:
    """The date typed in a show's alt text, if there is one and it is usable."""
    found = _words_dates(alt, today)
    for day, month, year in _NUMBERS_DATE.findall(alt):
        found.add(_resolve(int(day), int(month), int(year) if year else None, today))
    return _one(found)


def flyer_date(text: str, today: date) -> date | None:
    """The date in a flyer's OCR text. Only "day DE month" counts: bare numbers misread too easily."""
    return _one(_words_dates(text, today))


def title_from_alt(alt: str) -> str:
    """The alt text without its date and the separators left around it."""
    title = _ALT_DATE_TEXT.sub(" ", alt)
    title = re.sub(r"\s*/\s*(?:/\s*)+", " / ", title)
    return clean_text(title.strip(" @/-·"))


def _ocr(image: bytes, page_mode: str) -> str:
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "--psm", page_mode, "-l", "eng"],
        input=image, capture_output=True, timeout=OCR_TIMEOUT, check=False,
    )
    return result.stdout.decode("utf-8", errors="replace")


def agreed(readings: list[date | None]) -> date | None:
    """The date at least two OCR passes read, provided no pass read a different one. A single pass
    misreads a valid but wrong day (10 read as 19 on 2026-11-25); passes rarely agree on the same error."""
    found = [when for when in readings if when is not None]
    return found[0] if len(found) >= MIN_AGREEING and len(set(found)) == 1 else None


def _passes(image: bytes) -> list[bytes]:
    """The flyer enlarged, in colour and in grey, as PNG: each OCR pass reads one of them."""
    with Image.open(BytesIO(image)) as picture:
        size = (picture.width * OCR_SCALE, picture.height * OCR_SCALE)
        versions = [picture.convert("RGB"), ImageOps.grayscale(picture)]
        encoded = []
        for version in versions:
            png = BytesIO()
            version.resize(size, Image.Resampling.LANCZOS).save(png, format="PNG")
            encoded.append(png.getvalue())
    return encoded


def read_flyer(image: bytes, today: date) -> date | None:
    """The date printed on a flyer, by OCR, or None when Tesseract is missing or the passes do not agree."""
    if shutil.which("tesseract") is None:
        _log.warning("tesseract is not installed: flyers are not read")
        return None
    try:
        versions = _passes(image)
    except OSError:
        return None
    readings: list[date | None] = []
    for version in versions:
        for page_mode in OCR_PAGE_MODES:
            try:
                readings.append(flyer_date(_ocr(version, page_mode), today))
            except subprocess.TimeoutExpired:
                readings.append(None)
    return agreed(readings)


def _event(link: str, image: str, title: str, day: date, now: datetime) -> Event:
    starts_at = datetime(day.year, day.month, day.day, tzinfo=BA)
    slug = link.rstrip("/").rsplit("/", 1)[-1]
    return Event(
        id=f"palermogroove-{slug}-{day:%Y%m%d}",
        category=provisional_category(title, starts_at),
        title=title,
        venue=VENUE,
        city=city_name(None, CITY_OF_BUENOS_AIRES),
        region=CITY_OF_BUENOS_AIRES,
        country="AR",
        starts_at=starts_at,
        time_known=False,
        ticket_links=[TicketLink(vendor=VENDOR, url=link)],
        source_url=link,
        **source_image(image),
        updated_at=now,
    )


def scrape(
    regions: frozenset[str] | None = BUENOS_AIRES,
    delay: float = 2.0,
    transport: httpx.BaseTransport | None = None,
    now: datetime | None = None,
) -> list[Event]:
    """Read the home, then the flyer of each show whose text has no usable date, pausing `delay`
    seconds between requests. A home that fails stops the scrape (the runner reports it); a flyer
    that fails or cannot be read leaves its show out."""
    now = now or datetime.now(tz=BA)
    today = now.date()
    events: list[Event] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25, transport=transport) as client:
        shows = cards(client.get(SITE).raise_for_status().text)
        if len(shows) > MAX_SHOWS:
            raise ListingTooLongError(f"more than {MAX_SHOWS} shows; raise MAX_SHOWS")
        for link, image, alt in shows:
            day = alt_date(alt, today)
            if day is None:
                time.sleep(delay)
                try:
                    response = client.get(image)
                except httpx.HTTPError:
                    response = None
                if response is not None and response.status_code == 200:
                    day = read_flyer(response.content, today)
            if day is None:
                _log.warning("Palermo Groove: no date for %r (%s)", alt, link)
                continue
            events.append(_event(link, image, title_from_alt(alt), day, now))
    return events if regions is None else [e for e in events if e.region in regions]
