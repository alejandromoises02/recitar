"""Enigma Tickets: the home and the site's search list the shows (tours list theirs on their own page);
each show's page holds its dates in the Remix loader data, and its venue only as a Google Maps link.
Fixtures are real pages captured 2026-11-17, trimmed to the loader data the parser reads; the map
links' Location headers below are real too (cut after the coordinates)."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import enigma
from app.scrapers.enigma import (
    ListingTooLongError, event_data, listed, parse_event, region_of, scrape, venue_point,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)
CITY, CORDOBA = "Ciudad Autónoma de Buenos Aires", "Córdoba"
NATION = "dec75431-ad8f-4bc4-8533-c5849a4c3a5d"
PRIMAVERA = "7755c471-83a1-41a7-ab6a-a42538df09af"
QUILMES = "6832252d-60de-44f8-8329-b0cd3b6abcef"
GORILLAZ = "3fe80ea4-579d-45e7-80e4-8ee8cb49902b"
MISSLUPE = "9f75fe4f-9590-402b-9e82-cf7eb7902dab"
YERAI = "cbe9e664-7899-4a76-afae-337572531ac0"
GORILLAZ_TOUR = "3bb6d0b7-c5f5-4b3f-90ac-c72a3c12a1fe"
MAPS = {  # short link code -> Location it redirects to
    "JNgwEG7vaAwa7CgD9": "https://www.google.com.ar/maps/place/DESEO+CLUB/@-34.5844593,-58.4724213,17z/data=!3m1!4b1!4m6!3m5!1s0x95bcb7ed60d170b9:0x211107b16a646c97!8m2!3d-34.5844637!4d-58.4698464!16s%2Fg%2F11thr3qtl2",
    "1aZoCaPLdPLXXXkq5": "https://www.google.com.ar/maps/place/Eventos+Buenos+Aires+Club+Ciudad,+C1429+Buenos+Aires,+Provincia+de+Buenos+Aires/@-34.5427465,-58.4606951,17.25z/data=!4m6!3m5!1s0x95bcb4217056f1b3:0xb981c9d008cb3f3!8m2!3d-34.5423362!4d-58.4597883!16s%2Fm%2F05q40h",
    "oU7dAB6MVadWyGVeA": "https://www.google.com.ar/maps/place/Aparcamiento,+Ram%C3%B3n+C%C3%A1rcano+S%2FN,+X5000+C%C3%B3rdoba/@-31.368452,-64.2490402,16.5z/data=!4m6!3m5!1s0x94329ecc16e2f383:0x57bf8aed087422d!8m2!3d-31.3685071!4d-64.2474664!16s%2Fg%2F11jym09748",
    "5RrnC9mRjB7E2xzG9": "https://www.google.com/maps/place/Buenos+Aires/@-34.6158238,-58.4332985,12z/data=!3m1!4b1!4m6!3m5!1s0x95bcca3b4ef90cbd:0xa0b3812e88e88e87!8m2!3d-34.6036739!4d-58.3821215!16zL20vMDFseTVt",
    "zqvyhYKfc5fqZyR46": "https://www.google.com/maps/place/Casal+de+Catalunya/@-34.6182315,-58.3760196,15z/data=!4m6!3m5!1s0x95bccb2bb549d46d:0x901bafdb3d7adec3!8m2!3d-34.6182315!4d-58.3760196!16s%2Fg%2F11b6dn3gj6",
}
GEOREF_PROVINCES = {  # by latitude: Deseo, Club Ciudad, Kempes, "Argentina", Margarita Xirgu
    -34.5844637: CITY, -34.5423362: CITY, -31.3685071: CORDOBA, -34.6036739: CITY, -34.6182315: CITY,
}


def page(name: str) -> str:
    return (FIXTURES / f"enigma_{name}.html").read_text(encoding="utf-8")


def events(name: str, province: str | None = CITY, now: datetime = NOW):
    return parse_event(event_data(page(f"event_{name}")), province=province, now=now)


def test_a_concert_has_its_date_venue_region_and_official_page():
    [e] = events("nation")
    assert e.id == f"enigma-{NATION}-20261130T2030"
    assert (e.title, e.category) == ("NATION OF LANGUAGE & MANNEQUIN PUSSY", "concert")  # leading space dropped
    assert e.starts_at.isoformat() == "2026-11-30T20:30:00-03:00" and e.time_known  # "Lun 30/11 20:30hs"
    assert (e.venue, e.city, e.region, e.country) == ("Deseo Club", "Buenos Aires", "AR-C", "AR")
    url = f"https://www.enigmatickets.com/event/{NATION}"
    assert e.ticket_links[0].model_dump() == {"vendor": "Enigma Tickets", "url": url}
    assert e.source_url == url
    assert e.image_url == f"https://assets.prod.enigmatickets.com/events/images/{NATION}/large/current.jpg"
    assert e.image_origin == "source"


def test_a_pass_is_not_a_performance_but_each_day_is():
    days = events("primavera")
    assert [e.id for e in days] == [f"enigma-{PRIMAVERA}-20261128T0000", f"enigma-{PRIMAVERA}-20261129T0000"]
    assert {e.time_known for e in days} == {False}  # no time given; the "Abonos" have no date


def test_days_written_in_the_label_replace_a_placeholder_date():
    # Scheduled on 2027-04-01 and shown as "16, 17 y 18 DE ABRIL".
    days = events("quilmes")
    assert [e.starts_at.isoformat() for e in days] == [
        "2027-04-16T00:00:00-03:00", "2027-04-17T00:00:00-03:00", "2027-04-18T00:00:00-03:00",
    ]
    assert {e.time_known for e in days} == {False}


def test_each_date_of_a_show_is_an_event():
    assert sorted(e.id for e in events("yerai")) == [f"enigma-{YERAI}-20270422T0000", f"enigma-{YERAI}-20270424T0000"]


def test_a_show_outside_buenos_aires_takes_the_province_from_georef():
    [e] = events("gorillaz", province=CORDOBA)
    assert (e.region, e.city, e.starts_at.isoformat()) == ("AR-X", None, "2026-11-26T21:00:00-03:00")


def test_an_all_night_party_is_not_a_concert():
    [e] = events("misslupe")  # "Dom 06/12 23:59hs"
    assert e.category == "other"


def test_past_performances_are_dropped():
    assert events("primavera", now=datetime(2026, 11, 29, 9, 0, tzinfo=BA))[0].starts_at.day == 29  # today stays
    assert events("primavera", now=datetime(2026, 11, 30, tzinfo=BA)) == []
    assert events("nation", now=datetime(2026, 11, 30, 21, 0, tzinfo=BA)) == []


def test_a_page_without_a_show_has_no_event_data():
    assert event_data(page("not_found")) is None
    assert event_data("<html>no loader data</html>") is None
    assert parse_event(None, province=CITY, now=NOW) == []


def test_without_a_province_there_is_no_region():
    [e] = events("nation", province=None)
    assert (e.region, e.city) == (None, None)


@pytest.mark.parametrize("province, region", [
    ("Ciudad Autónoma de Buenos Aires", "AR-C"),
    ("Buenos Aires", "AR-B"),
    ("Córdoba", "AR-X"),
    ("Chubut", "AR-U"),
    (None, None),
])
def test_region_from_the_georef_province(province, region):
    assert region_of(province) == region


def test_the_venue_point_is_the_place_pin_of_the_map_link():
    assert venue_point(MAPS["JNgwEG7vaAwa7CgD9"]) == (-34.5844637, -58.4698464)  # not the view centre after "@"
    assert venue_point(MAPS["oU7dAB6MVadWyGVeA"]) == (-31.3685071, -64.2474664)
    assert venue_point("https://www.google.com/maps/place/Somewhere") is None
    assert venue_point(None) is None


def test_listing_pages_list_their_shows_and_tours():
    shows, tours = listed(page("home"))
    assert len(shows) == 21 and tours == {GORILLAZ_TOUR}  # 22 cards, the tour among them
    shows, tours = listed(page("search"))
    assert len(shows) == 20 and tours == {GORILLAZ_TOUR}  # page 1 of 21 cards
    assert listed(page("tour_gorillaz")) == ({PRIMAVERA, GORILLAZ}, set())
    assert listed("<html></html>") == (set(), set())


class FakeEnigma:
    """Serves the home, the search (page 1 by GET, later pages by POST as the site's own script does),
    tour and show pages by id, the venues' map short links, and Georef's ubicacion."""

    def __init__(self, home: str, search: list[str], tours: dict[str, str], shows: dict[str, str]):
        self.home, self.search, self.tours, self.shows = home, search, tours, shows
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(f"{request.method} {request.url}")
        host, path = request.url.host, request.url.path
        if path == "/georef/api/ubicacion":
            name = GEOREF_PROVINCES[float(request.url.params["lat"])]
            return httpx.Response(200, json={"ubicacion": {"provincia": {"nombre": name}}})
        if host == "maps.app.goo.gl":
            return httpx.Response(302, headers={"Location": MAPS[path.strip("/")]})
        if host != "www.enigmatickets.com":
            return httpx.Response(500)  # nothing else should be requested
        if path == "/":
            return httpx.Response(200, text=self.home)
        if path == "/search/event" and request.method == "GET":
            return httpx.Response(200, text=self.search[0])
        if path == "/search/event" and request.method == "POST":
            assert request.url.params["_data"] == "routes/search.event"
            form = dict(pair.split("=") for pair in request.content.decode().split("&"))
            assert form["pageSize"] == "21"
            number = int(form["page"])
            return httpx.Response(200, text=self.search[number - 1] if number <= len(self.search) else "[]")
        if path.startswith("/tour/"):
            return httpx.Response(200, text=self.tours.get(path[len("/tour/"):], ""))
        if path.startswith("/event/") and path[len("/event/"):] in self.shows:
            return httpx.Response(200, text=self.shows[path[len("/event/"):]])
        return httpx.Response(500, text=page("not_found"))


def site() -> FakeEnigma:
    return FakeEnigma(
        home=page("home"),
        search=[page("search"), (FIXTURES / "enigma_search_page2.json").read_text(encoding="utf-8")],
        tours={GORILLAZ_TOUR: page("tour_gorillaz")},
        shows={
            NATION: page("event_nation"), PRIMAVERA: page("event_primavera"), QUILMES: page("event_quilmes"),
            GORILLAZ: page("event_gorillaz"), MISSLUPE: page("event_misslupe"), YERAI: page("event_yerai"),
        },
    )


@pytest.fixture
def no_wait(monkeypatch):
    monkeypatch.setattr(enigma.time, "sleep", lambda _s: None)
    monkeypatch.setattr(enigma, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))


def test_scrape_reads_the_home_search_pages_and_tours_and_keeps_buenos_aires(no_wait):
    fake = site()
    found = scrape(delay=0, transport=httpx.MockTransport(fake))
    assert sorted((e.id, e.region) for e in found) == sorted([
        (f"enigma-{NATION}-20261130T2030", "AR-C"),
        (f"enigma-{PRIMAVERA}-20261128T0000", "AR-C"),
        (f"enigma-{PRIMAVERA}-20261129T0000", "AR-C"),
        (f"enigma-{QUILMES}-20270416T0000", "AR-C"),
        (f"enigma-{QUILMES}-20270417T0000", "AR-C"),
        (f"enigma-{QUILMES}-20270418T0000", "AR-C"),
        (f"enigma-{MISSLUPE}-20261206T2359", "AR-C"),
        (f"enigma-{YERAI}-20270422T0000", "AR-C"),  # only on the search's second page
        (f"enigma-{YERAI}-20270424T0000", "AR-C"),
    ])  # Gorillaz plays Córdoba; the other shows fail to load and are skipped
    assert sum(r == "POST https://www.enigmatickets.com/search/event?_data=routes%2Fsearch.event" for r in fake.requests) == 1
    assert sum(f"/tour/{GORILLAZ_TOUR}" in r for r in fake.requests) == 1
    assert sum(f"/event/{GORILLAZ_TOUR}" in r for r in fake.requests) == 0  # a tour is not a show
    assert sum("JNgwEG7vaAwa7CgD9" in r for r in fake.requests) == 1  # Deseo once for its two shows
    assert sum("ubicacion" in r for r in fake.requests) == 5  # once per venue
    assert not any("google.com" in r for r in fake.requests)  # the redirect is read, not followed


def test_every_region_is_kept_on_request(no_wait):
    found = scrape(regions=None, delay=0, transport=httpx.MockTransport(site()))
    assert [(e.venue, e.region) for e in found if e.id.startswith(f"enigma-{GORILLAZ}")] == [
        ("Playón Norte Estadio Mario Alberto Kempes", "AR-X"),
    ]


def test_a_venue_without_coordinates_has_no_region(no_wait):
    fake = site()

    def broken_maps(request: httpx.Request) -> httpx.Response:
        if request.url.host == "maps.app.goo.gl":
            raise httpx.ConnectError("down")
        return fake(request)

    found = scrape(regions=None, delay=0, transport=httpx.MockTransport(broken_maps))
    assert found and {e.region for e in found} == {None}


def test_the_requests_say_who_we_are(no_wait):
    fake = site()
    agents = set()

    def spy(request: httpx.Request) -> httpx.Response:
        agents.add(request.headers["user-agent"])
        return fake(request)

    scrape(delay=0, transport=httpx.MockTransport(spy))
    assert agents == {"recitAR-research/0.1"}


def test_a_failing_listing_stops_the_scrape(no_wait):
    fake = site()
    fake.tours = {}

    def no_tours(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503) if request.url.path.startswith("/tour/") else fake(request)

    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=httpx.MockTransport(no_tours))


def test_too_many_show_pages_stop_the_scrape(no_wait, monkeypatch):
    monkeypatch.setattr(enigma, "MAX_SHOW_PAGES", 2)
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site()))


def test_a_search_that_never_ends_stops_the_scrape(no_wait):
    fake = site()
    fake.search = [page("search")] + [(FIXTURES / "enigma_search_page2.json").read_text(encoding="utf-8").replace("[", "[" + ",".join(["{}"] * 20) + ",", 1)] * 100
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(fake))


def test_every_event_carries_the_pin_of_its_venue_map_link(no_wait):
    found = scrape(regions=None, delay=0, transport=httpx.MockTransport(site()))
    assert {e.venue: e.venue_point for e in found} == {
        "Deseo Club": (-34.5844637, -58.4698464),
        "Club Ciudad": (-34.5423362, -58.4597883),
        "Playón Norte Estadio Mario Alberto Kempes": (-31.3685071, -64.2474664),
        "Argentina": (-34.6036739, -58.3821215),  # a city's pin; the placeholder is never stored (repository)
        "Teatro Margarita Xirgu": (-34.6182315, -58.3760196),
    }
