"""All Access: the home, the site's search (capped at 50 results) and each venue's page list the shows;
each show's page holds its performances in App.bootstrapData. Fixtures are real pages captured
2026-11-17; show pages are trimmed to that one script."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import allaccess
from app.scrapers.allaccess import (
    ListingTooLongError, coordinates, event_data, event_slugs, parse_event, region_of, scrape, venue_link,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)
RIVER = (-34.5465963, -58.4484825)
CITY, PROVINCE = "Ciudad Autónoma de Buenos Aires", "Buenos Aires"
GEOREF_PROVINCES = {  # by latitude: River, The Roxy Bar & Grill, Huracán, Hipódromo de San Isidro
    -34.5465963: CITY, -34.5805116: CITY, -34.643524: CITY, -34.4819238: PROVINCE,
}


def page(name: str) -> str:
    return (FIXTURES / f"allaccess_{name}.html").read_text(encoding="utf-8")


def events(name: str, slug: str, province: str | None = None, now: datetime = NOW):
    return parse_event(event_data(page(name)), slug, province=province, now=now)


def test_a_concert_has_its_date_venue_region_and_official_page():
    [e] = events("airbag", "airbag", province="Ciudad Autónoma de Buenos Aires")
    assert e.id == "allaccess-airbag-20261211T2100"
    assert (e.title, e.category) == ("AIRBAG", "concert")
    assert e.starts_at.isoformat() == "2026-12-11T21:00:00-03:00" and e.time_known  # stored as 00:00 UTC
    assert (e.venue, e.city, e.region, e.country) == ("Estadio River Plate", "Buenos Aires", "AR-C", "AR")
    assert e.ticket_links[0].model_dump() == {"vendor": "All Access", "url": "https://www.allaccess.com.ar/event/airbag"}
    assert e.source_url == "https://www.allaccess.com.ar/event/airbag"
    assert e.image_url.startswith("https://cdn.getcrowder.com/images/cc4021a6") and e.image_origin == "source"


def test_a_pass_is_not_a_performance_but_each_day_is():
    days = events("lollapalooza", "lollapalooza-2027", province="Buenos Aires")
    assert [e.starts_at.isoformat() for e in days] == [
        "2027-03-12T11:00:00-03:00", "2027-03-13T11:00:00-03:00", "2027-03-14T11:00:00-03:00",
    ]  # the "Abono" has no date
    assert {(e.region, e.time_known) for e in days} == {("AR-B", False)}  # named "Día 1", not a time


def test_a_show_without_performances_yet_gives_nothing():
    assert events("no_shows", "karol-g-viajando-por-el-mundo") == []


def test_parking_is_not_a_show():
    assert events("parking", "estacionamiento-u2", province="Ciudad Autónoma de Buenos Aires") == []


def test_a_sold_out_show_is_kept():
    [e] = events("sold_out", "bingo-musical-edicion-hitazos-80-90-00", province="Ciudad Autónoma de Buenos Aires")
    assert e.starts_at.isoformat() == "2026-11-25T20:00:00-03:00"


def test_past_performances_are_dropped():
    assert events("airbag", "airbag", now=datetime(2026, 12, 12, tzinfo=BA)) == []


def test_a_page_without_a_show_has_no_event_data():
    assert event_data(page("gone")) is None
    assert parse_event(None, "gone", province=None, now=NOW) == []


def test_without_georef_the_address_gives_the_region():
    [e] = events("huracan", "slipknot-venta-general")  # city "CABA", province "Buenos Aires"
    assert (e.region, e.city) == ("AR-C", "Buenos Aires")


@pytest.mark.parametrize("city, province, region", [
    ("CABA", "CABA", "AR-C"),
    ("CABA", "Buenos Aires", "AR-C"),
    ("CABA", "Ciudad Autonoma de Buenos Aires", "AR-C"),
    ("Mar del Plata", "Buenos Aires", "AR-B"),
    ("Bahía Blanca", "Provincia de Buenos Aires", "AR-B"),
    ("San Isidro, Buenos Aires", None, "AR-B"),
    ("Cordoba", "Cordoba", "AR-X"),
    ("Antártida Argentina 3901, Q8304JES Neuquén", "Antártida Argentina 3901, Q8304JES Neuquén", None),
])
def test_region_from_the_address(city, province, region):
    assert region_of(city, province) == region


def test_the_venue_page_and_coordinates_come_from_the_show():
    data = event_data(page("airbag"))
    assert venue_link(data) == "estadio-river"
    assert coordinates(data) == RIVER
    assert venue_link(event_data(page("huracan"))) is None  # Huracán has no page of its own


def test_listing_pages_link_their_shows():
    home = event_slugs(page("home"))
    assert {"airbag", "karol-g-viajando-por-el-mundo", "lollapalooza-2027", "slipknot"} <= home
    assert len(event_slugs(page("search_f"))) == 36  # "36 eventos encontrados"
    assert len(event_slugs(page("venue_vorterix"))) == 25  # "25 eventos encontrados"


class FakeAllAccess:
    """Serves the home, searches by text, venue pages, show pages by slug, and Georef's ubicacion."""

    def __init__(self, home: str, searches: dict[str, str], venues: dict[str, str], shows: dict[str, str]):
        self.home, self.searches, self.venues, self.shows = home, searches, venues, shows
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        path = request.url.path
        if path == "/georef/api/ubicacion":
            name = GEOREF_PROVINCES[float(request.url.params["lat"])]
            return httpx.Response(200, json={"ubicacion": {"provincia": {"nombre": name}}})
        if path == "/":
            return httpx.Response(200, text=self.home)
        if path.startswith("/list/"):
            return httpx.Response(200, text=self.searches.get(path[len("/list/"):], "<p>0 eventos encontrados</p>"))
        if path.startswith("/venue/"):
            return httpx.Response(200, text=self.venues.get(path[len("/venue/"):], ""))
        if path.startswith("/event/"):
            return httpx.Response(200, text=self.shows.get(path[len("/event/"):], page("gone")))
        return httpx.Response(404)


def links(*slugs: str) -> str:
    return "".join(f"<a href='/event/{s}'>{s}</a>" for s in slugs)


def site() -> FakeAllAccess:
    return FakeAllAccess(
        home=links("airbag", "karol-g-viajando-por-el-mundo", "lollapalooza-2027", "gone-show"),
        searches={"a": links("airbag", "estacionamiento-u2"), "s": links("slipknot-venta-general")},
        venues={"estadio-river": links("airbag", "bingo-musical-edicion-hitazos-80-90-00")},
        shows={
            "airbag": page("airbag"), "karol-g-viajando-por-el-mundo": page("no_shows"),
            "lollapalooza-2027": page("lollapalooza"), "estacionamiento-u2": page("parking"),
            "bingo-musical-edicion-hitazos-80-90-00": page("sold_out"),
            "slipknot-venta-general": page("huracan"),
            "slipknot-venta-general-vip-packages": page("huracan"),  # the same show listed again
        },
    )


@pytest.fixture
def no_wait(monkeypatch):
    monkeypatch.setattr(allaccess.time, "sleep", lambda _s: None)
    monkeypatch.setattr(allaccess, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))


def test_scrape_reads_the_home_searches_and_venue_pages_and_keeps_buenos_aires(no_wait):
    fake = site()
    fake.searches["v"] = links("slipknot-venta-general-vip-packages")
    found = scrape(delay=0, transport=httpx.MockTransport(fake))
    assert sorted((e.id, e.region) for e in found) == [
        ("allaccess-airbag-20261211T2100", "AR-C"),
        ("allaccess-bingo-musical-edicion-hitazos-80-90-00-20261125T2000", "AR-C"),  # only on River's page
        ("allaccess-lollapalooza-2027-20270312T1100", "AR-B"),
        ("allaccess-lollapalooza-2027-20270313T1100", "AR-B"),
        ("allaccess-lollapalooza-2027-20270314T1100", "AR-B"),
        ("allaccess-slipknot-venta-general-20270908T2100", "AR-C"),  # its VIP listing is the same show
    ]  # parking and a show without dates give nothing; "gone-show" has no data
    searched = {u.rsplit("/", 1)[-1] for u in fake.requests if "/list/" in u}
    assert searched == set("abcdefghijklmnopqrstuvwxyz0123456789")
    assert sum("/venue/estadio-river" in u for u in fake.requests) == 1
    ubicacion = [u for u in fake.requests if "ubicacion" in u]
    assert len(ubicacion) == 4  # River, Roxy, San Isidro, Huracán: once per venue


def test_a_georef_failure_falls_back_to_the_address(no_wait):
    fake = site()

    def no_georef(request: httpx.Request) -> httpx.Response:
        if "georef" in request.url.path:
            raise httpx.ConnectError("down")
        return fake(request)

    found = scrape(delay=0, transport=httpx.MockTransport(no_georef))
    assert {(e.venue, e.region) for e in found} == {
        ("Estadio River Plate", "AR-C"), ("The Roxy Bar & Grill", "AR-C"),
        ("Hipodromo de San Isidro", "AR-B"), ("Estadio Huracán", "AR-C"),
    }


def test_the_requests_say_who_we_are(no_wait):
    fake = site()
    agents = set()

    def spy(request: httpx.Request) -> httpx.Response:
        agents.add(request.headers["user-agent"])
        return fake(request)

    scrape(delay=0, transport=httpx.MockTransport(spy))
    assert agents == {"recitAR-research/0.1"}


def test_too_many_show_pages_stop_the_scrape(no_wait, monkeypatch):
    monkeypatch.setattr(allaccess, "MAX_SHOW_PAGES", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site()))
