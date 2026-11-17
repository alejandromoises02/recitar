"""Coolco (a Palco4 shop): the main page's cards list the shows; each show's page holds its performances
in the sessions widget's JSON and its venue in `dataLayerP4`. Fixtures are real pages captured
2026-11-17: the main page trimmed to its lines that link a page, show pages to the lines the parser reads."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import coolco
from app.scrapers.coolco import ListingTooLongError, parse_show, region_of, scrape, show_slugs

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)
SHOW_URL = "https://ticketing.coolco.io/tickets-ar/es/"


def page(name: str) -> str:
    return (FIXTURES / f"coolco_{name}.html").read_text(encoding="utf-8")


def test_a_show_has_its_date_venue_region_and_official_page():
    [e] = parse_show(page("simple_plan"), "simple-plan-obr-2026", now=NOW)
    assert e.id == "coolco-simple-plan-obr-2026-20270511T2100"
    assert (e.title, e.category) == ("Simple Plan - The Bigger Than You Think!", "concert")  # venue not appended
    assert e.starts_at.isoformat() == "2027-05-11T21:00:00-03:00" and e.time_known
    assert (e.venue, e.city, e.region, e.country) == ("Estadio Obras Sanitarias", "Buenos Aires", "AR-C", "AR")
    url = SHOW_URL + "simple-plan-obr-2026"
    assert e.ticket_links[0].model_dump() == {"vendor": "Coolco", "url": url}
    assert e.source_url == url
    assert e.image_url == "https://d2r4j3zfvrmx80.cloudfront.net/tickets-ar/img_web/5/6/220/m_poster.jpg"
    assert e.image_origin == "source"


def test_each_performance_is_an_event():
    days = parse_show(page("el_plan"), "el-plan-obr-2026", now=NOW)
    assert [e.id for e in days] == [
        "coolco-el-plan-obr-2026-20261210T2100", "coolco-el-plan-obr-2026-20261211T2100",
    ]
    assert {e.title for e in days} == {"El Plan de la Mariposa"}


def test_spaces_in_the_title_are_collapsed():
    [e] = parse_show(page("till_lindemann"), "till-lindemann-obr-2027", now=NOW)
    assert e.title == "Till Lindemann - World Tour 2027"  # published as "Till Lindemann -  World Tour 2027"


def test_past_performances_are_dropped():
    [e] = parse_show(page("el_plan"), "el-plan-obr-2026", now=datetime(2026, 12, 11, 12, 0, tzinfo=BA))
    assert e.id.endswith("20261211T2100")


def test_a_page_without_a_show_gives_nothing():
    assert parse_show(page("no_show"), "no-show", now=NOW) == []
    assert parse_show("", "empty", now=NOW) == []


@pytest.mark.parametrize("city, state, region", [
    ("CABA", "Buenos Aires", "AR-C"),
    ("Ciudad Autónoma de Buenos Aires", "", "AR-C"),
    ("La Plata", "Buenos Aires", "AR-B"),
    ("Rosario", "Santa Fe", "AR-S"),
])
def test_region_from_the_address(city, state, region):
    assert region_of(city, state) == region


def test_the_main_page_links_its_nine_shows_and_nothing_else():
    assert show_slugs(page("main")) == {
        "daniel-caesar-obr-2026", "deny-obr-2027", "el-plan-obr-2026", "la-kermesse-obr-2026",
        "nestor-en-bloque-obr-2026", "nuestro-romance-obr", "saramalacara-obr-2026",
        "simple-plan-obr-2026", "till-lindemann-obr-2027",
    }  # not main, legalConditions, registroUsuario, comprarEvento...


def card(slug: str, language: str = "es") -> str:
    return f"""<div class="item-wrapper" onclick="window.location.href='https://ticketing.coolco.io/tickets-ar/{language}/{slug}'">"""


class FakeCoolco:
    """Serves the main page and show pages by slug; an unknown slug redirects to main, as the site does."""

    def __init__(self, main: str, shows: dict[str, str]):
        self.main, self.shows = main, shows
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == "/tickets-ar/es/main":
            return httpx.Response(200, text=self.main)
        if path.startswith("/tickets-ar/es/") and path.rsplit("/", 1)[-1] in self.shows:
            return httpx.Response(200, text=self.shows[path.rsplit("/", 1)[-1]])
        return httpx.Response(302, headers={"Location": "https://ticketing.coolco.io/tickets-ar/main"})


@pytest.fixture
def no_wait(monkeypatch):
    monkeypatch.setattr(coolco.time, "sleep", lambda _s: None)
    monkeypatch.setattr(coolco, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))


def site() -> FakeCoolco:
    return FakeCoolco(
        main=card("simple-plan-obr-2026") + card("el-plan-obr-2026", "en") + card("gone-obr-2026"),
        shows={"simple-plan-obr-2026": page("simple_plan"), "el-plan-obr-2026": page("el_plan")},
    )


def test_scrape_reads_the_main_page_then_each_show(no_wait):
    fake = site()
    found = scrape(delay=0, transport=httpx.MockTransport(fake))
    assert sorted(e.id for e in found) == [
        "coolco-el-plan-obr-2026-20261210T2100",
        "coolco-el-plan-obr-2026-20261211T2100",
        "coolco-simple-plan-obr-2026-20270511T2100",
    ]  # "gone-obr-2026" redirects to main: skipped
    assert sorted(str(r.url) for r in fake.requests) == [
        SHOW_URL + "el-plan-obr-2026", SHOW_URL + "gone-obr-2026", SHOW_URL + "main", SHOW_URL + "simple-plan-obr-2026",
    ]  # shows linked in English are read from their Spanish page
    assert {e.source_url for e in found} == {SHOW_URL + "el-plan-obr-2026", SHOW_URL + "simple-plan-obr-2026"}


def test_scrape_keeps_only_the_regions_asked_for(no_wait):
    assert scrape(regions=frozenset({"AR-X"}), delay=0, transport=httpx.MockTransport(site())) == []


def test_a_failing_show_page_is_skipped(no_wait):
    fake = site()

    def flaky(request: httpx.Request) -> httpx.Response:
        if "simple-plan" in request.url.path:
            return httpx.Response(500)
        return fake(request)

    assert {e.id.rsplit("-", 1)[0] for e in scrape(delay=0, transport=httpx.MockTransport(flaky))} == {
        "coolco-el-plan-obr-2026",
    }


def test_a_failing_main_page_stops_the_scrape(no_wait):
    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=httpx.MockTransport(lambda request: httpx.Response(503)))


def test_the_requests_say_who_we_are(no_wait):
    fake = site()
    scrape(delay=0, transport=httpx.MockTransport(fake))
    assert {r.headers["user-agent"] for r in fake.requests} == {"recitAR-research/0.1"}


def test_waits_between_requests(monkeypatch, no_wait):
    pauses: list[float] = []
    monkeypatch.setattr(coolco.time, "sleep", pauses.append)
    scrape(delay=2.0, transport=httpx.MockTransport(site()))
    assert pauses == [2.0] * 4  # main and three shows


def test_too_many_shows_stop_the_scrape(monkeypatch, no_wait):
    monkeypatch.setattr(coolco, "MAX_SHOW_PAGES", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site()))
