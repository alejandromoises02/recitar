"""Pulso Tickets: the home redirects to the only public event, or lists several; each event's tickets
page holds its performances, venue, address and coordinates. Fixtures are real pages captured
2026-11-17: the home's 302 body as served, and the tickets page trimmed to the parts the parser reads.
No home listing several events could be captured (the site had one); that case is built from the
event links as the real pages write them."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import pulso
from app.scrapers.pulso import ListingTooLongError, coordinates, event_slugs, parse_event, region_of, scrape

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)
CITY = "Ciudad Autónoma de Buenos Aires"
HOME = "https://pulsotickets.com/evento/popfest-1015"
POPFEST_DATE = "sáb., 05 dic. 2026 - 13:00 hs"


def page(name: str) -> str:
    return (FIXTURES / f"pulso_{name}.html").read_text(encoding="utf-8")


def popfest(**replace: str) -> str:
    text = page("popfest_tickets")
    for old, new in replace.items():
        assert old in text  # the edit must hit the real markup
        text = text.replace(old, new)
    return text


def two_days() -> str:
    """The real performance card, repeated for a second day without a time."""
    text = page("popfest_tickets")
    start = text.index('<div class="p-6 rounded-lg shadow-md')
    end = text.index("</h3>", start) + len("</h3>")
    card = text[start:end]
    return text[:end] + card.replace(POPFEST_DATE, "dom., 06 dic. 2026").replace("01M17AKS", "02SECOND") + text[end:]


def events(text: str, slug: str = "popfest-1015", province: str | None = CITY, now: datetime = NOW):
    return parse_event(text, slug, province=province, now=now)


def test_a_festival_day_has_its_date_time_venue_region_and_official_page():
    [e] = events(page("popfest_tickets"))
    assert e.id == "pulso-popfest-1015-20261205T1300"
    assert (e.title, e.category) == ("PopFest 101.5", "concert")  # "Música & Recitales"
    assert e.starts_at.isoformat() == "2026-12-05T13:00:00-03:00" and e.time_known
    assert (e.venue, e.city, e.region, e.country) == ("Parque Norte", "Buenos Aires", "AR-C", "AR")
    assert e.ticket_links[0].model_dump() == {"vendor": "Pulso Tickets", "url": HOME}
    assert e.source_url == HOME
    assert e.image_url == "https://pulsotickets.com/storage/funciones-images/01M17AKS4058E4KMY42B20Q37B.webp"
    assert e.image_origin == "source"


def test_each_performance_is_an_event_and_a_missing_time_is_not_known():
    first, second = events(two_days())
    assert (first.starts_at.isoformat(), first.time_known) == ("2026-12-05T13:00:00-03:00", True)
    assert (second.id, second.starts_at.isoformat(), second.time_known) == (
        "pulso-popfest-1015-20261206T0000", "2026-12-06T00:00:00-03:00", False,
    )
    assert first.image_url.endswith("/01M17AKS4058E4KMY42B20Q37B.webp")  # each card's own image
    assert second.image_url.endswith("/02SECOND4058E4KMY42B20Q37B.webp")


def test_the_same_performance_twice_is_one_event():
    text = two_days().replace("dom., 06 dic. 2026", POPFEST_DATE)
    assert len(events(text)) == 1


def test_past_performances_are_dropped():
    assert events(page("popfest_tickets"), now=datetime(2026, 12, 5, 13, 1, tzinfo=BA)) == []
    [later] = events(two_days(), now=datetime(2026, 12, 5, 13, 1, tzinfo=BA))
    assert later.starts_at.day == 6


@pytest.mark.parametrize("category, expected", [
    ("Teatro", "theatre"), ("Stand Up", "other"), ("Música &amp; Recitales", "concert"),
    ("Música", "concert"),  # assumed: only "Música & Recitales" was seen
])
def test_the_site_category_decides_the_kind(category, expected):
    [e] = events(popfest(**{"item_category: 'Música &amp; Recitales'": f"item_category: '{category}'"}))
    assert e.category == expected


@pytest.mark.parametrize("broken", [
    {"<h1 class=\"text-xl sm:text-2xl font-bold text-gray-900\">PopFest 101.5</h1>": ""},  # no title
    {POPFEST_DATE: "Fecha a confirmar"},  # no date
    {'<p class="text-xl font-bold text-slate-900">Parque Norte</p>': ""},  # no venue
])
def test_a_page_missing_what_an_event_needs_gives_nothing(broken):
    assert events(popfest(**broken)) == []


def test_without_georef_the_address_gives_the_region():
    [e] = events(page("popfest_tickets"), province=None)  # "..., CABA"
    assert (e.region, e.city) == ("AR-C", "Buenos Aires")


@pytest.mark.parametrize("address, region", [
    ("Av. Cantilo y Guiraldes (frente a Ciudad Universitaria)., CABA", "AR-C"),
    ("Av. Corrientes 1234, Ciudad Autónoma de Buenos Aires", "AR-C"),
    ("Calle 7 776, La Plata, Buenos Aires", "AR-B"),
    ("Bv. Oroño 1000, Rosario, Santa Fe", "AR-S"),
    ("Sin datos", None),
])
def test_region_from_the_address(address, region):
    assert region_of(address) == region


def test_coordinates_come_from_the_map_link():
    assert coordinates(page("popfest_tickets")) == (-34.5483276, -58.438253)
    assert coordinates(popfest(**{"query=-34.5483276,-58.438253": "query=Parque+Norte"})) is None


def test_the_home_redirect_names_the_only_event():
    assert event_slugs(page("home_redirect")) == ["popfest-1015"]
    assert event_slugs("", location="https://www.pulsotickets.com/evento/popfest-1015") == ["popfest-1015"]


def test_a_home_listing_several_events_links_each_once():
    home = (
        '<a href="https://pulsotickets.com/evento/popfest-1015">PopFest</a>'
        '<a href="https://pulsotickets.com/evento/popfest-1015/tickets">Entradas</a>'
        '<a href="https://www.pulsotickets.com/evento/otro-show-2027/tickets">Entradas</a>'
        '<a href="/evento/tercero?utm_source=x">Tercero</a>'
    )
    assert event_slugs(home) == ["popfest-1015", "otro-show-2027", "tercero"]


class FakePulso:
    """Serves the home (a 302 or a listing), tickets pages by slug, and Georef's ubicacion."""

    def __init__(self, home: httpx.Response, tickets: dict[str, str]):
        self.home, self.tickets = home, tickets
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        path = request.url.path
        if path == "/georef/api/ubicacion":
            return httpx.Response(200, json={"ubicacion": {"provincia": {"nombre": CITY}}})
        if path == "/":
            return self.home
        if path.startswith("/evento/") and path.endswith("/tickets"):
            slug = path[len("/evento/"):-len("/tickets")]
            return httpx.Response(200, text=self.tickets[slug]) if slug in self.tickets else httpx.Response(404)
        if path.startswith("/evento/"):
            return httpx.Response(200, text="the 2.3 MB landing; never needed")
        return httpx.Response(404)


def redirect_home() -> httpx.Response:
    return httpx.Response(302, headers={"Location": HOME}, text=page("home_redirect"))


@pytest.fixture
def no_wait(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(pulso.time, "sleep", sleeps.append)
    monkeypatch.setattr(pulso, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))
    return sleeps


def test_scrape_follows_the_home_redirect_to_the_only_event(no_wait):
    fake = FakePulso(redirect_home(), {"popfest-1015": page("popfest_tickets")})
    [e] = scrape(delay=2.0, transport=httpx.MockTransport(fake))
    assert (e.id, e.region) == ("pulso-popfest-1015-20261205T1300", "AR-C")
    site = [u for u in fake.requests if "georef" not in u]
    assert site == ["https://pulsotickets.com/", "https://pulsotickets.com/evento/popfest-1015/tickets"]
    assert no_wait == [2.0, 2.0]  # after each request to the site


def test_scrape_reads_every_event_a_listing_home_links_and_keeps_buenos_aires(no_wait):
    rosario = popfest(**{
        "Av. Cantilo y Guiraldes (frente a Ciudad Universitaria)., CABA": "Bv. Oroño 1000, Rosario, Santa Fe",
        "query=-34.5483276,-58.438253": "query=Rosario",
    })
    home = httpx.Response(200, text=(
        '<a href="https://pulsotickets.com/evento/popfest-1015">a</a>'
        '<a href="https://pulsotickets.com/evento/fest-rosario">b</a>'
        '<a href="https://pulsotickets.com/evento/gone">c</a>'
    ))
    fake = FakePulso(home, {"popfest-1015": two_days(), "fest-rosario": rosario})
    found = scrape(delay=0, transport=httpx.MockTransport(fake))
    assert [e.id for e in found] == ["pulso-popfest-1015-20261205T1300", "pulso-popfest-1015-20261206T0000"]
    everywhere = scrape(regions=None, delay=0, transport=httpx.MockTransport(fake))
    assert {e.region for e in everywhere} == {"AR-C", "AR-S"}  # "gone" answers 404 and is skipped


def test_a_failing_home_stops_the_scrape(no_wait):
    fake = FakePulso(httpx.Response(500), {})
    with pytest.raises(httpx.HTTPStatusError):
        scrape(delay=0, transport=httpx.MockTransport(fake))


def test_the_requests_say_who_we_are(no_wait):
    fake = FakePulso(redirect_home(), {"popfest-1015": page("popfest_tickets")})
    agents = set()

    def spy(request: httpx.Request) -> httpx.Response:
        agents.add(request.headers["user-agent"])
        return fake(request)

    scrape(delay=0, transport=httpx.MockTransport(spy))
    assert agents == {"recitAR-research/0.1"}


def test_too_many_event_pages_stop_the_scrape(no_wait, monkeypatch):
    monkeypatch.setattr(pulso, "MAX_EVENT_PAGES", 1)
    home = httpx.Response(200, text='<a href="/evento/a">a</a><a href="/evento/b">b</a>')
    with pytest.raises(ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(FakePulso(home, {})))


def test_every_event_carries_the_coordinates_of_the_map_link():
    found = events(page("popfest_tickets"))
    assert found and {e.venue_point for e in found} == {(-34.5483276, -58.438253)}
