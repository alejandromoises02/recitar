"""Palermo Groove: its home lists every show as a Passline flyer whose alt text is the title, usually
with the date. Shows without a date in the text get it read from the flyer by OCR, under strict
rules, or are left out. Fixtures are real: the home captured whole on 2026-11-25 (26 shows) and four
of its flyers."""

import shutil
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import palermogroove
from app.scrapers.palermogroove import (
    ListingTooLongError,
    agreed,
    alt_date,
    cards,
    flyer_date,
    read_flyer,
    scrape,
    title_from_alt,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 25, 12, 0, tzinfo=BA)
TODAY = NOW.date()
HOME = (FIXTURES / "palermogroove_home.html").read_text(encoding="utf-8")
FLYER_HOST = "imagenes.passline.com"
needs_tesseract = pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract is not installed")


def flyer(name: str) -> bytes:
    return (FIXTURES / f"palermogroove_flyer_{name}.jpg").read_bytes()


def test_the_home_lists_each_show_with_its_passline_link_flyer_and_alt_text():
    found = cards(HOME)
    assert len(found) == 26
    assert found[2] == (
        "https://www.passline.com/eventos/fiesta-clandestina-pier-banda-sorpresa-27112026",
        "https://imagenes.passline.com/eventos/-815716-rec.jpg",
        "Fiesta Clandestina - PIER + VIEJAS LOCASxF&A @ 27.11.2026",
    )
    assert len({link for link, _, _ in found}) == 26


@pytest.mark.parametrize(("alt", "expected"), [
    ("Fiesta Clandestina - PIER + VIEJAS LOCASxF&A @ 27.11.2026", date(2026, 11, 27)),
    ("ABAPALOOZA 28/11 LA DESPEDIDA", date(2026, 11, 28)),
    ("Sundays by Groove @ Domingo 29 de noviembre de 2026", date(2026, 11, 29)),
    ("Tekgen Rave Culture @ Groove 5.12.2026", date(2026, 12, 5)),
    ("Heavy Noise Festival 2026 - Solidario @ 27..12.2026", date(2026, 12, 27)),
    # no year: the next time that day comes
    ("VIOLETA HODAR EN BUENOS AIRES / 19.2 / GROOVE", date(2027, 2, 19)),
])
def test_a_date_written_in_the_alt_text_is_read(alt, expected):
    assert alt_date(alt, TODAY) == expected


@pytest.mark.parametrize("alt", [
    "Mass Of The Fermenting Dregs en Argentina",
    "CHEQUEFEST 2026 @ GROOVE",  # a year alone is not a date
    "A.N.I.M.A.L. - 30 Años de El Nuevo Camino del Hombre (Solidario)",
    "CAIBO en Groove @ 21.02.2026",  # already past: a typo for 2027, not to be trusted
    "Fiesta @ 31.02.2027",  # no such day
])
def test_no_usable_date_in_the_alt_text_gives_none(alt):
    assert alt_date(alt, TODAY) is None


@pytest.mark.parametrize(("alt", "title"), [
    ("Flaco Vazquez en Groove @ 11.12.2026", "Flaco Vazquez en Groove"),
    ("ABAPALOOZA 28/11 LA DESPEDIDA", "ABAPALOOZA LA DESPEDIDA"),
    ("Sundays by Groove @ Domingo 29 de noviembre de 2026", "Sundays by Groove"),
    ("VIOLETA HODAR EN BUENOS AIRES / 19.2 / GROOVE", "VIOLETA HODAR EN BUENOS AIRES / GROOVE"),
    ("Sleeping With Sirens - Único Show en Argentina", "Sleeping With Sirens - Único Show en Argentina"),
])
def test_the_title_is_the_alt_text_without_its_date(alt, title):
    assert title_from_alt(alt) == title


# OCR text as Tesseract 5 printed it for the real flyers on 2026-11-25.
@pytest.mark.parametrize(("text", "expected"), [
    ("MASS OF THE FERMENTING DREGS OUR LUNES 24 DE MAYO 2027 BUENOS AIRES . GROOVE AVENIDA SANTA FE 4389",
     date(2027, 5, 24)),
    ("bf Libel anes oe SLEEPING SIRENS MIERCOLES 9 DE DICIEMBRE BUENOS AIRES - GROOVE ANTIOPRDAS",
     date(2026, 12, 9)),
    ("LATIN AMERICA TOUR 2026 10 dE DICIEMBRE PALERMO GROOVE (AV. SANTA FE 4389, CABA)", date(2026, 12, 10)),
])
def test_a_clear_day_and_month_in_the_flyer_text_is_read(text, expected):
    assert flyer_date(text, TODAY) == expected


@pytest.mark.parametrize("text", [
    "TAT in AMBRICA TOUR 2026 +0 DE DICIEMBRE PALERMO GROOVE",  # the day was misread
    "MARTES 9 DE DICIEMBRE GROOVE",  # 9 December 2026 is a Wednesday: one of the two is misread
    "10 DE DICIEMBRE Y 11 DE DICIEMBRE",  # two dates: which is this show's?
    "GROOVE AV SANTA FE 4389 19.12",  # bare numbers from OCR are too easy to misread
    "LUNES 24 DE MAYO 2021",  # past
    "",
])
def test_an_unclear_flyer_text_gives_none(text):
    assert flyer_date(text, TODAY) is None


@needs_tesseract
def test_ocr_reads_the_date_on_a_real_flyer():
    assert read_flyer(flyer("mass"), TODAY) == date(2027, 5, 24)
    assert read_flyer(flyer("sleeping"), TODAY) == date(2026, 12, 9)


@needs_tesseract
def test_a_flyer_read_as_two_different_days_gives_none():
    # Slaughter To Prevail plays on 10 December; one OCR pass reads "19 DE DICIEMBRE", another "10".
    assert read_flyer(flyer("slaughter"), TODAY) is None


@needs_tesseract
def test_a_flyer_the_ocr_cannot_read_gives_none_rather_than_a_guess():
    # The day on Pacifica's flyer (19 December) is set in boxed letters Tesseract does not read.
    assert read_flyer(flyer("pacifica"), TODAY) is None


@pytest.mark.parametrize(("readings", "expected"), [
    ([date(2026, 12, 9), None, date(2026, 12, 9)], date(2026, 12, 9)),
    ([date(2026, 12, 19), date(2026, 12, 10), date(2026, 12, 10)], None),  # passes disagree
    ([None, date(2026, 12, 10), None], None),  # one pass alone is not enough
    ([None, None], None),
])
def test_a_flyer_date_needs_two_passes_and_no_disagreement(readings, expected):
    assert agreed(readings) == expected


def test_ocr_without_tesseract_gives_none(monkeypatch):
    monkeypatch.setattr(palermogroove.shutil, "which", lambda _name: None)
    assert read_flyer(flyer("mass"), TODAY) is None


def site(home: httpx.Response, flyers: dict[str, bytes], requested: list[str]) -> httpx.MockTransport:
    def answer(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if request.url.host == "www.palermogroove.com.ar" and request.url.path == "/":
            return home
        if request.url.host == FLYER_HOST and request.url.path in flyers:
            return httpx.Response(200, content=flyers[request.url.path])
        return httpx.Response(404)
    return httpx.MockTransport(answer)


def test_scrape_keeps_dated_shows_reads_undated_flyers_and_leaves_out_the_unreadable(monkeypatch):
    read: list[bytes] = []
    dates = {b"mass": date(2027, 5, 24)}

    def fake_read_flyer(image: bytes, today: date) -> date | None:
        read.append(image)
        return dates.get(image)

    monkeypatch.setattr(palermogroove, "read_flyer", fake_read_flyer)
    requested: list[str] = []
    transport = site(httpx.Response(200, text=HOME), {
        "/eventos/mass-of-the-fermenting-dregs-en-argentina-547151-rec.jpg": b"mass",
    }, requested)
    events = scrape(delay=0, transport=transport, now=NOW)

    by_id = {e.id: e for e in events}
    flaco = by_id["palermogroove-flaco-vazquez-en-groove-11122026-20261211"]
    assert flaco.title == "Flaco Vazquez en Groove"
    assert flaco.venue == "Palermo Groove"
    assert (flaco.city, flaco.region, flaco.country) == ("Buenos Aires", "AR-C", "AR")
    assert (flaco.starts_at, flaco.time_known) == (datetime(2026, 12, 11, tzinfo=BA), False)
    assert flaco.category == "concert"
    assert [(link.vendor, str(link.url)) for link in flaco.ticket_links] == [
        ("Passline", "https://www.passline.com/eventos/flaco-vazquez-en-groove-11122026"),
    ]
    assert flaco.source_url == "https://www.passline.com/eventos/flaco-vazquez-en-groove-11122026"
    assert (flaco.image_url, flaco.image_origin) == (
        "https://imagenes.passline.com/eventos/flaco-vazquez-en-groove-11122026-570914-rec.jpg", "source")

    mass = by_id["palermogroove-mass-of-the-fermenting-dregs-en-argentina-20270524"]
    assert (mass.title, mass.starts_at) == ("Mass Of The Fermenting Dregs en Argentina", datetime(2027, 5, 24, tzinfo=BA))

    # 14 shows carry a usable date in the text; Mass is read from its flyer; the other 11 are left out.
    assert len(events) == 15
    assert "Sleeping With Sirens - Único Show en Argentina" not in {e.title for e in events}
    # Only the flyers of the 12 shows without a usable date are fetched.
    flyers_fetched = [url for url in requested if FLYER_HOST in url]
    assert len(flyers_fetched) == 12
    assert flaco.image_url not in flyers_fetched
    assert read == [b"mass"]  # the other flyers answered 404: nothing to read


def test_a_home_that_fails_stops_the_scrape():
    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=site(httpx.Response(503), {}, []), now=NOW)


def test_a_home_longer_than_expected_stops_the_scrape(monkeypatch):
    monkeypatch.setattr(palermogroove, "MAX_SHOWS", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=site(httpx.Response(200, text=HOME), {}, []), now=NOW)
