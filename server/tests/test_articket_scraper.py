"""Articket: a search for each vowel lists every show as a card (title, venue, city, province); each
category is its own listing; a show's page lists its performances in a <select>. Fixtures are real
pages captured 2026-11-17: the listing trimmed to its cards, show pages to their og meta and dates."""

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import articket
from app.scrapers.articket import (
    Card, ListingTooLongError, cards, category_of, city_spellings, parse_show, performances, scrape, show_image,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)


def page(name: str) -> str:
    return (FIXTURES / f"articket_{name}.html").read_text(encoding="utf-8")


LISTING = page("listing")
CARDS = {c.slug: c for c in cards(LISTING)}


def card_markup(*slugs: str) -> str:
    """The real listing's cards for these slugs, as a listing page of their own."""
    chunks = re.split(r'(?=<div id="caja-\d+")', LISTING)
    return "".join(c for c in chunks if any(f'href="/{s}/"' in c for s in slugs))


def events(name: str, slug: str, listed_under: set[str] = frozenset({"Recitales"}), now: datetime = NOW):
    card = CARDS[slug]
    return parse_show(page(name), card, listed_under=set(listed_under), city=card.city, now=now)


def test_the_listing_has_a_card_per_show():
    assert len(CARDS) == 68  # "let cantidadEventos = 68"; "Ver más" only unhides cards already in the page
    assert CARDS["IVAN-NOBLE-EN-VORTERIX"] == Card(
        slug="IVAN-NOBLE-EN-VORTERIX", title="IVAN NOBLE EN VORTERIX", venue="Vorterix",
        city="MAR DEL PLATA", province="BUENOS AIRES",
        image="https://articket.com.ar/media/imagenes_eventos/home/2026/08/mdq1.jpeg",
    )


def test_a_venue_name_keeps_its_quotes_and_commas_split_from_the_right():
    card = CARDS["LA-GRANJA-EL-RECITAL-EN-MACIA-26-11"]
    assert (card.venue, card.city, card.province) == ('Teatro Municipal "Jorge Alfredo Alasino"', "Macia", "Entre Rios")
    markup = card_markup("IVAN-NOBLE-EN-VORTERIX").replace('alt="Vorterix,', 'alt="Vorterix, Sala 2,')
    [card] = cards(markup)
    assert (card.venue, card.city, card.province) == ("Vorterix, Sala 2", "MAR DEL PLATA", "BUENOS AIRES")


def test_a_concert_has_its_date_venue_region_and_official_page():
    [e] = events("ivan_noble", "IVAN-NOBLE-EN-VORTERIX")
    assert e.id == "articket-ivan-noble-en-vorterix-20261204T2130"
    assert (e.title, e.category) == ("IVAN NOBLE EN VORTERIX", "concert")
    assert e.starts_at.isoformat() == "2026-12-04T21:30:00-03:00" and e.time_known
    assert (e.venue, e.city, e.region, e.country) == ("Vorterix", "MAR DEL PLATA", "AR-B", "AR")
    url = "https://articket.com.ar/IVAN-NOBLE-EN-VORTERIX/"
    assert e.ticket_links[0].model_dump() == {"vendor": "Articket", "url": url}
    assert e.source_url == url
    assert e.image_url == "https://articket.com.ar/media/imagenes_eventos/detalle/2026/08/mdq1.jpeg"
    assert e.image_origin == "source"


def test_each_date_of_a_show_is_a_performance():
    dates = events("zambayonny", "ZAMBAYONNY-CICLO-VERANO")
    assert [e.starts_at.isoformat() for e in dates] == [
        "2027-01-09T21:00:00-03:00", "2027-01-16T21:00:00-03:00",
        "2027-01-23T21:00:00-03:00", "2027-01-30T21:00:00-03:00",
    ]  # "09 01 2027, 21:00hs"; the "Seleccione una Fecha" placeholder is not a date
    assert len({e.id for e in dates}) == 4


def test_past_performances_are_dropped():
    assert events("bioparque", "BIOPARQUE-BATAN--NOVIEMBRE-", listed_under={"Parques"}) == []  # 01-11-2026
    later = datetime(2027, 1, 20, tzinfo=BA)
    assert [e.starts_at.day for e in events("zambayonny", "ZAMBAYONNY-CICLO-VERANO", now=later)] == [23, 30]


def test_a_date_without_a_time():
    [(starts_at, time_known)] = performances('<select id="idFechasEventos"><option value="1">05-12-2026</option></select>')
    assert (starts_at.isoformat(), time_known) == ("2026-12-05T00:00:00-03:00", False)


def test_a_page_without_dates_or_a_card_without_a_venue_gives_nothing():
    assert performances("<html></html>") == []
    assert parse_show("<html></html>", CARDS["IVAN-NOBLE-EN-VORTERIX"], listed_under=set(), city=None, now=NOW) == []
    no_venue = Card(slug="X", title="X", venue="", city=None, province=None, image=None)
    assert parse_show(page("ivan_noble"), no_venue, listed_under=set(), city=None, now=NOW) == []


def test_without_an_image_on_the_show_page_the_card_image_is_used():
    assert show_image("<html></html>") is None
    card = CARDS["IVAN-NOBLE-EN-VORTERIX"]
    [e] = parse_show(page("ivan_noble").replace('property="og:image"', ""), card, listed_under=set(), city=None, now=NOW)
    assert e.image_url == card.image


@pytest.mark.parametrize("slug, region", [
    ("IVAN-NOBLE-EN-VORTERIX", "AR-B"),
    ("BIOPARQUE-BATAN--NOVIEMBRE-", "AR-B"),
    ("ESPIRITUAL-DAY-UN-DIA-PARA-RECONECTAR", "AR-B"),  # "Buenos aires"
    ("AGENCIA-DE-PLACERES-EN-ROSARIO", "AR-S"),
    ("RM2-San-Paranoia-Inv-RHYSE-22", "AR-Q"),
    ("LA-GRANJA-EL-RECITAL-EN-NOGOYA-28-11", "AR-E"),
    ("MUERDE-LUCIANO-CACERES-EN-ARIAS", "AR-X"),
])
def test_region_from_the_card_location(slug, region):
    card = CARDS[slug]
    show = page("ivan_noble")
    [e] = parse_show(show, card, listed_under=set(), city=card.city, now=NOW)
    assert e.region == region


def test_a_city_takes_its_most_common_spelling_not_in_capitals():
    spellings = city_spellings(CARDS.values())
    assert spellings["mar del plata"] == "Mar del Plata"  # 35 cards, against 13 "MAR DEL PLATA" and one "Mar del plata"
    assert spellings["batan"] == "Batan"
    capitals = [Card(slug=str(i), title="X", venue="V", city="MAR DEL PLATA", province=None, image=None) for i in range(3)]
    assert city_spellings([*capitals, CARDS["IVAN-NOBLE-EN-VORTERIX"]])["mar del plata"] == "MAR DEL PLATA"
    assert city_spellings([*capitals, CARDS["CUMBIA-GRANDE-EN-EL-TRI"]])["mar del plata"] == "Mar del Plata"


@pytest.mark.parametrize("listed_under, title, expected", [
    ({"Recitales"}, "IVAN NOBLE EN VORTERIX", "concert"),
    ({"Recitales"}, "ROSE GUN TRIBUTE EN VORTERIX", "tribute"),
    ({"Recitales"}, "FIESTA RICOTERA FUNDAMENTALISTA EN ABBEY ROAD", "other"),
    ({"Teatros"}, "MUERDE - LUCIANO CACERES", "theatre"),
    ({"Infantiles"}, "LA GRANJA EL RECITAL", "theatre"),
    ({"Fiestas"}, "CARIBE FEST EN ABBEY ROAD", "other"),
    ({"Convención"}, "CONGRESO SE PUDRE 2026", "other"),
    ({"Parques"}, "BIOPARQUE BATAN", "other"),
    (set(), "CUMBIA GRANDE EN EL TRI", "other"),  # under no category
    ({"Deporte"}, "TORNEO", None),
    ({"Deporte", "Recitales"}, "TORNEO", None),
])
def test_category_from_the_listings_a_show_is_under(listed_under, title, expected):
    assert category_of(listed_under, title, datetime(2026, 12, 4, 21, 30, tzinfo=BA)) == expected


def test_a_tribute_listed_under_concerts():
    [e] = events("rose_gun", "ROSE-GUN-TRIBUTE-EN-VORTERIX")
    assert e.category == "tribute"


def test_an_all_night_party_listed_under_theatre_is_theatre():
    dates = events("mar_del_enciende", "MAR-DEL-ENCIENDE-RECARGADO", listed_under={"Teatros"})
    assert len(dates) == 5 and {e.category for e in dates} == {"theatre"}
    assert [e.starts_at.strftime("%H:%M") for e in dates] == ["21:00", "23:59", "23:59", "23:59", "23:59"]


SHOWS = {
    "IVAN-NOBLE-EN-VORTERIX": "ivan_noble", "ZAMBAYONNY-CICLO-VERANO": "zambayonny",
    "BIOPARQUE-BATAN--NOVIEMBRE-": "bioparque", "ROSE-GUN-TRIBUTE-EN-VORTERIX": "rose_gun",
    "AGENCIA-DE-PLACERES-EN-ROSARIO": "ivan_noble",
}


class FakeArticket:
    """Serves the search by `buscar`, the listings by `categoria`, and show pages by slug. A show it
    does not know redirects home, as the site does."""

    def __init__(self, searches: dict[str, str], categories: dict[str, str], shows: dict[str, str]):
        self.searches, self.categories, self.shows = searches, categories, shows
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path, query = request.url.path, parse_qs(request.url.query.decode(), keep_blank_values=True)
        if path == "/" and "buscar" in query:
            return httpx.Response(200, text=self.searches.get(query["buscar"][0], ""))
        if path == "/" and "categoria" in query:
            return httpx.Response(200, text=self.categories.get(query["categoria"][0], ""))
        slug = path.strip("/")
        if path == f"/{slug}/" and slug in self.shows:
            return httpx.Response(200, text=page(self.shows[slug]))
        return httpx.Response(301, headers={"Location": "https://articket.com.ar/"})


def site() -> FakeArticket:
    return FakeArticket(
        searches={
            "a": card_markup("IVAN-NOBLE-EN-VORTERIX", "AGENCIA-DE-PLACERES-EN-ROSARIO", "BIOPARQUE-BATAN--NOVIEMBRE-"),
            "e": card_markup("IVAN-NOBLE-EN-VORTERIX", "ROSE-GUN-TRIBUTE-EN-VORTERIX", "CUMBIA-GRANDE-EN-EL-TRI"),
        },
        categories={
            "Recitales": card_markup("IVAN-NOBLE-EN-VORTERIX", "ROSE-GUN-TRIBUTE-EN-VORTERIX"),
            "Teatros": card_markup("ZAMBAYONNY-CICLO-VERANO", "AGENCIA-DE-PLACERES-EN-ROSARIO"),
            "Parques": card_markup("BIOPARQUE-BATAN--NOVIEMBRE-"),
        },
        shows=SHOWS,
    )


@pytest.fixture
def no_wait(monkeypatch):
    monkeypatch.setattr(articket.time, "sleep", lambda _s: None)
    monkeypatch.setattr(articket, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))


def test_scrape_reads_the_searches_and_categories_then_each_show_and_keeps_buenos_aires(no_wait):
    fake = site()
    found = scrape(delay=0, transport=httpx.MockTransport(fake))
    assert sorted((e.id, e.category, e.city) for e in found) == [
        ("articket-ivan-noble-en-vorterix-20261204T2130", "concert", "Mar del Plata"),  # card says "MAR DEL PLATA"
        ("articket-rose-gun-tribute-en-vorterix-20261212T2030", "tribute", "Mar del Plata"),
        ("articket-zambayonny-ciclo-verano-20270109T2100", "theatre", "Mar del Plata"),  # only under Teatros
        ("articket-zambayonny-ciclo-verano-20270116T2100", "theatre", "Mar del Plata"),
        ("articket-zambayonny-ciclo-verano-20270123T2100", "theatre", "Mar del Plata"),
        ("articket-zambayonny-ciclo-verano-20270130T2100", "theatre", "Mar del Plata"),
    ]  # Rosario is not Buenos Aires; the bioparque's date is past; the cumbia show's page is gone
    params = [dict(r.url.params) for r in fake.requests if r.url.path == "/"]
    assert [p["buscar"] for p in params if "buscar" in p] == list("aeiou")
    assert {p["categoria"] for p in params if "categoria" in p} == set(articket.CATEGORIES)
    shows = [r.url.path for r in fake.requests if r.url.path != "/"]
    assert len(shows) == len(set(shows)) == 6  # each show once, ending in "/"


def test_all_regions(no_wait):
    found = scrape(regions=None, delay=0, transport=httpx.MockTransport(site()))
    assert ("articket-agencia-de-placeres-en-rosario-20261204T2130", "AR-S", "theatre") in {
        (e.id, e.region, e.category) for e in found
    }


def test_a_failing_listing_stops_the_scrape(no_wait):
    fake = site()

    def broken(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("categoria") == "Teatros":
            return httpx.Response(500)
        return fake(request)

    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=httpx.MockTransport(broken))


def test_a_failing_show_page_is_skipped(no_wait):
    fake = site()

    def broken(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/ZAMBAYONNY-CICLO-VERANO/":
            raise httpx.ReadTimeout("slow")
        if request.url.path == "/ROSE-GUN-TRIBUTE-EN-VORTERIX/":
            return httpx.Response(500)
        return fake(request)

    found = scrape(delay=0, transport=httpx.MockTransport(broken))
    assert [e.id for e in found] == ["articket-ivan-noble-en-vorterix-20261204T2130"]


def test_the_requests_say_who_we_are(no_wait):
    fake = site()
    scrape(delay=0, transport=httpx.MockTransport(fake))
    assert {r.headers["user-agent"] for r in fake.requests} == {"recitAR-research/0.1"}


def test_it_waits_between_requests(monkeypatch, no_wait):
    waits = []
    monkeypatch.setattr(articket.time, "sleep", waits.append)
    fake = site()
    scrape(delay=2.0, transport=httpx.MockTransport(fake))
    assert waits == [2.0] * len(fake.requests)


def test_too_many_show_pages_stop_the_scrape(no_wait, monkeypatch):
    monkeypatch.setattr(articket, "MAX_SHOW_PAGES", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site()))
