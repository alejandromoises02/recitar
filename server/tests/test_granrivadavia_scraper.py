"""Teatro Gran Rivadavia: its cartelera links one page per show, each with its performances and the
Fullticket link that sells it. Fixtures are the real pages, captured whole on 2026-11-24 (3 shows);
the unknown one is what /evento/99999/x answers."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import granrivadavia
from app.scrapers.granrivadavia import ListingTooLongError, event_paths, parse_event, scrape

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 24, 12, 0, tzinfo=BA)
SITE = "https://www.granrivadavia.com.ar"
EUROPE = "/evento/577/EUROPE"


def page(name: str) -> str:
    return (FIXTURES / f"granrivadavia_{name}.html").read_text(encoding="utf-8")


def europe(**replace: str) -> str:
    text = page("event_europe")
    for old, new in replace.items():
        assert old in text  # the edit must hit the real markup
        text = text.replace(old, new)
    return text


def test_the_cartelera_links_each_show_once_in_order():
    assert event_paths(page("cartelera")) == [
        "/evento/575/PAZ-MARTINEZ", "/evento/576/Canticuenticos", "/evento/577/EUROPE",
    ]


def test_a_show_page_gives_its_performance_venue_and_fullticket_link():
    [event] = parse_event(page("event_europe"), EUROPE, now=NOW)
    assert event.id == "granrivadavia-577-20270416T2100"
    assert event.title == "EUROPE"
    assert event.venue == "Teatro Gran Rivadavia"
    assert (event.city, event.region, event.country) == ("Buenos Aires", "AR-C", "AR")
    assert event.starts_at == datetime(2027, 4, 16, 21, 0, tzinfo=BA)
    assert event.time_known is True
    assert event.category == "concert"
    assert [(link.vendor, str(link.url)) for link in event.ticket_links] == [
        ("Fullticket", "https://fullticket.com/tickets/es/entradas-musica-europe"),
    ]
    assert str(event.source_url) == f"{SITE}{EUROPE}/"
    assert str(event.image_url) == f"{SITE}/imagenes/eventos/577.jpg"
    assert event.image_origin == "source"


def test_a_theatre_link_makes_a_theatre_show():
    [event] = parse_event(page("event_canticuenticos"), "/evento/576/Canticuenticos", now=NOW)
    assert event.category == "theatre"
    assert event.starts_at == datetime(2026, 11, 29, 16, 0, tzinfo=BA)


def test_each_listed_performance_is_one_event():
    second = '<div class="col-xs-6 col-sm-4 col-md-2">16.abr.27 / 21.00</div>'
    text = europe(**{second: second + '<div class="col-xs-6 col-sm-4 col-md-2">17.abr.27 / 20.30</div>'})
    events = parse_event(text, EUROPE, now=NOW)
    assert [e.id for e in events] == ["granrivadavia-577-20270416T2100", "granrivadavia-577-20270417T2030"]


def test_a_performance_without_a_time_keeps_its_day():
    performance = '<div class="col-xs-6 col-sm-4 col-md-2">16.abr.27 / 21.00</div>'
    text = europe(**{performance: '<div class="col-xs-6 col-sm-4 col-md-2">16.abr.27</div>'})
    [event] = parse_event(text, EUROPE, now=NOW)
    assert (event.id, event.starts_at, event.time_known) == (
        "granrivadavia-577-20270416T0000", datetime(2027, 4, 16, tzinfo=BA), False)


def test_a_performance_that_started_is_dropped():
    assert parse_event(page("event_paz_martinez"), "/evento/575/PAZ-MARTINEZ",
                       now=datetime(2026, 11, 28, 21, 1, tzinfo=BA)) == []


def test_a_show_not_on_sale_yet_links_the_venue_page():
    text = europe(**{"https://fullticket.com/tickets/es/entradas-musica-europe": "#"})
    [event] = parse_event(text, EUROPE, now=NOW)
    assert [(link.vendor, str(link.url)) for link in event.ticket_links] == [("Teatro Gran Rivadavia", f"{SITE}{EUROPE}/")]
    assert event.category == "concert"


def test_an_unknown_show_page_gives_nothing():
    assert parse_event(page("event_unknown"), "/evento/99999/x", now=NOW) == []


def pages(responses: dict[str, httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(lambda request: responses.get(request.url.path, httpx.Response(404)))


def test_scrape_reads_the_cartelera_then_each_show_and_skips_one_that_fails():
    transport = pages({
        "/cartelera/": httpx.Response(200, text=page("cartelera")),
        # the site answers a show's path without the trailing slash with a redirect
        "/evento/575/PAZ-MARTINEZ/": httpx.Response(200, text=page("event_paz_martinez")),
        "/evento/576/Canticuenticos/": httpx.Response(500),
        f"{EUROPE}/": httpx.Response(200, text=page("event_europe")),
    })
    events = scrape(delay=0, transport=transport, now=NOW)
    assert [e.id for e in events] == ["granrivadavia-575-20261128T2100", "granrivadavia-577-20270416T2100"]


def test_a_cartelera_that_fails_stops_the_scrape():
    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=pages({"/cartelera/": httpx.Response(503)}))


def test_a_cartelera_longer_than_expected_stops_the_scrape(monkeypatch):
    monkeypatch.setattr(granrivadavia, "MAX_EVENT_PAGES", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=pages({"/cartelera/": httpx.Response(200, text=page("cartelera"))}))
