"""TuEntrada: the search page (a date range, page by page) lists the shows, each category is its own
search, and each show's page holds one session per performance. Fixtures are real pages captured
2026-11-17, trimmed to the payload scripts the scraper reads."""

from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import tuentrada
from app.scrapers.tuentrada import (
    category_listing_path, category_of, coordinates, date_listing_path, listing_page, parse_show, region_of, scrape,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=BA)
IMAGE = "https://bucket.tuentrada.com/bucket/events/virus/virus-image-main.jpg"


def page(name: str) -> str:
    return (FIXTURES / f"tuentrada_{name}.html").read_text(encoding="utf-8")


def show(name: str, slug: str, listed_under=frozenset({"música"}), province="Buenos Aires", now=NOW, image=IMAGE):
    return parse_show(page(name), slug, listed_under=set(listed_under), image=image, province=province, now=now)


def test_a_concert_has_its_date_venue_region_and_official_page():
    [e] = show("virus", "virus-tgi")
    assert e.id == "tuentrada-virus-tgi-20261128T2100"
    assert (e.title, e.category) == ("Virus", "concert")
    assert e.starts_at.isoformat() == "2026-11-28T21:00:00-03:00" and e.time_known
    assert (e.venue, e.city, e.region, e.country) == ("Teatro Gran Ituzaingó", "Ituzaingó", "AR-B", "AR")
    assert e.ticket_links[0].model_dump() == {"vendor": "TuEntrada", "url": "https://www.tuentrada.com/virus-tgi"}
    assert e.source_url == "https://www.tuentrada.com/virus-tgi"
    assert (e.image_url, e.image_origin) == (IMAGE, "source")


def test_every_session_is_its_own_date_and_past_ones_are_dropped():
    starts = [e.starts_at.isoformat() for e in show("luciano_pereyra", "luciano-pereyra-tgr", province="Ciudad Autónoma de Buenos Aires")]
    assert starts == [
        "2027-04-02T20:30:00-03:00", "2027-04-03T20:30:00-03:00", "2027-04-04T20:00:00-03:00",
        "2027-04-09T20:30:00-03:00", "2027-04-10T20:30:00-03:00", "2027-04-11T20:00:00-03:00",
    ]
    later = show("luciano_pereyra", "luciano-pereyra-tgr", now=datetime(2027, 4, 10, 12, tzinfo=BA))
    assert [e.starts_at.isoformat() for e in later] == ["2027-04-10T20:30:00-03:00", "2027-04-11T20:00:00-03:00"]


def test_the_city_of_buenos_aires_is_the_city():
    e = show("luciano_pereyra", "luciano-pereyra-tgr", province="Ciudad Autónoma de Buenos Aires")[0]
    assert (e.region, e.city) == ("AR-C", "Buenos Aires")


def test_a_pass_is_not_a_performance():
    # "Abono 2 Dias" shares the first day's date; only the two days are performances.
    events = show("pack", "taninos-wine-fest-2026", listed_under=set(), province="Mendoza")
    assert [(e.title, e.starts_at.isoformat()) for e in events] == [
        ("Taninos Winefest 2026", "2026-11-27T19:00:00-03:00"), ("Taninos Winefest 2026", "2026-11-28T19:00:00-03:00"),
    ]
    assert {e.region for e in events} == {"AR-M"}


def test_a_sold_out_show_is_still_a_show():
    assert len(show("sold_out", "abel-pintos-tgr", province="Ciudad Autónoma de Buenos Aires")) == 2


def test_a_page_without_sessions_gives_nothing():
    assert show("search_first", "ntvg-gira") == []


def test_without_an_image_the_event_has_none():
    [e] = show("virus", "virus-tgi", image=None)
    assert (e.image_url, e.image_origin) == (None, None)


@pytest.mark.parametrize("listed_under, category", [
    ({"música"}, "concert"),
    ({"jazz/blues"}, "concert"),
    ({"festivales de música"}, "concert"),
    ({"teatro"}, "theatre"),
    ({"familia"}, "theatre"),
    ({"una categoría nueva"}, "other"),
    (set(), "other"),
    ({"música", "teatro"}, "concert"),
    ({"deportes"}, None),
])
def test_each_tuentrada_category_maps_to_ours(listed_under, category):
    assert category_of(listed_under, "Virus", datetime(2026, 11, 28, 21, tzinfo=BA)) == category


def test_a_party_listed_under_music_is_other():
    assert category_of({"música"}, "Fiesta Bresh", datetime(2026, 11, 28, 23, 59, tzinfo=BA)) == "other"


def test_a_tribute_listed_under_music_is_a_tribute():
    assert category_of({"música"}, "Dm Experience", datetime(2026, 11, 28, 21, tzinfo=BA)) == "tribute"


def test_sports_are_left_out():
    assert show("virus", "virus-tgi", listed_under={"deportes"}) == []


@pytest.mark.parametrize("city, province, region", [
    ("Ituzaingó", "Buenos Aires", "AR-B"),
    ("Buenos Aires", "Ciudad Autónoma de Buenos Aires", "AR-C"),
    ("Maipú", "Mendoza", "AR-M"),
    ("Buenos Aires", None, "AR-C"),  # every venue TuEntrada files under "Buenos Aires" was in the city
    ("CABA", None, "AR-C"),
    ("Neuquén", None, "AR-Q"),  # a province's name, as the city of its capital
    ("Ituzaingó", None, None),  # no province and a city that names none: unknown, so not shown
])
def test_region_of(city, province, region):
    assert region_of(city, province) == region


def test_the_venue_coordinates_are_read_from_the_page():
    assert coordinates(page("virus")) == (-34.66049613164969, -58.66711872545106)
    assert coordinates(page("search_first")) is None


def test_the_map_placeholder_is_not_the_venue():
    # A venue without its own entry (in Escobar) gets a map pinned on the Obelisco.
    assert '"latitude":"-34.60369786376767","longitude":"-58.38160363203237"' in tuentrada.payload(page("placeholder_map"))
    assert coordinates(page("placeholder_map")) is None


def test_a_listing_page_gives_its_entries_and_the_next_page():
    entries, following = listing_page(page("search_first"))
    assert [(e["slug"], e["model"]) for e in entries][:2] == [("ntvg-gira", "eventGroup"), ("museodelagua", "event")]
    assert len(entries) == 6
    assert following.startswith("/busqueda?desde=17-11-2026&hasta=31-12-2029&cursor=")


def test_the_last_listing_page_links_nowhere():
    entries, following = listing_page(page("search_last"))
    assert [e["slug"] for e in entries][-1] == "this-is-michael-2027-tgr" and following is None


def test_listing_paths():
    assert date_listing_path(NOW) == "/busqueda?desde=17-11-2026&hasta=16-11-2029"
    assert category_listing_path("música") == "/busqueda?categoria=m%C3%BAsica"
    assert category_listing_path("jazz/blues") == "/busqueda?categoria=jazz%2Fblues"


def _listing_html(entries: list[dict], following: str | None) -> str:
    """A search page shaped like the real one: the entries in a payload script, then the pager."""
    import json

    data = json.dumps(["$", "$L1b", None, {"events": entries, "itemsParams": []}])
    anchor = f'<a aria-label="Go to next page" href="{following or "#"}"><span>Siguiente</span></a>'
    return f"<html><body>{anchor}<script>self.__next_f.push([1,{json.dumps('1b:' + data)}])</script></body></html>"


class FakeTuEntrada:
    """Serves each search (by its query) page by page through a cursor, show pages by slug, and Georef."""

    def __init__(
        self, searches: dict[str, list[list[dict]]], pages: dict[str, str], provinces: dict[tuple, str],
        localities: dict[str, list[str]] | None = None,
    ):
        self.searches, self.pages, self.provinces, self.localities = searches, pages, provinces, localities or {}
        self.requests: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        if request.url.path == "/georef/api/localidades":
            found = self.localities.get(request.url.params["nombre"], [])
            return httpx.Response(200, json={"cantidad": len(found), "localidades": [{"provincia": {"nombre": n}} for n in found]})
        if request.url.path == "/georef/api/ubicacion":
            point = (float(request.url.params["lat"]), float(request.url.params["lon"]))
            name = self.provinces.get(point)
            return httpx.Response(200, json={"ubicacion": {"provincia": {"nombre": name} if name else None}})
        if request.url.path == "/busqueda":
            query = parse_qs(urlsplit(str(request.url)).query)
            key = query["categoria"][0] if "categoria" in query else "fechas"
            index = int(query.get("cursor", ["0"])[0])
            pages = self.searches.get(key, [[]])
            following = None
            if index + 1 < len(pages):
                base = f"categoria={query['categoria'][0]}" if "categoria" in query else "desde=a&amp;hasta=b"
                following = f"/busqueda?{base}&amp;cursor={index + 1}"
            return httpx.Response(200, text=_listing_html(pages[index], following))
        slug = request.url.path.lstrip("/")
        if slug in self.pages:
            return httpx.Response(200, text=self.pages[slug])
        return httpx.Response(307, headers={"location": "https://www.tuentrada.com/"})


def test_scrape_walks_every_page_reads_each_show_and_keeps_buenos_aires(monkeypatch):
    ituzaingo, gran_rex = (-34.66049613164969, -58.66711872545106), (-34.603210654064206, -58.37885587483365)
    site = FakeTuEntrada(
        searches={
            "fechas": [
                [{"slug": "ntvg-gira", "model": "eventGroup"}, {"slug": "virus-tgi", "model": "event"}],
                [{"slug": "luciano-pereyra-tgr", "model": "event"}, {"slug": "gone-tgr", "model": "event"}],
                [{"slug": "taninos-wine-fest-2026", "model": "event"}, {"slug": "abel-pintos-tgr", "model": "event"}],
            ],
            "música": [[{"slug": "virus-tgi", "model": "event"}], [{"slug": "luciano-pereyra-tgr", "model": "event"}]],
            "deportes": [[{"slug": "abel-pintos-tgr", "model": "event"}]],
        },
        pages={
            "virus-tgi": page("virus"), "luciano-pereyra-tgr": page("luciano_pereyra"),
            "taninos-wine-fest-2026": page("pack"), "abel-pintos-tgr": page("sold_out"),
        },
        provinces={ituzaingo: "Buenos Aires", gran_rex: "Ciudad Autónoma de Buenos Aires"},
    )
    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    monkeypatch.setattr(tuentrada, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))
    events = scrape(delay=0, transport=httpx.MockTransport(site))
    assert sorted({(e.id.rsplit("-", 1)[0], e.category, e.region) for e in events}) == [
        ("tuentrada-luciano-pereyra-tgr", "concert", "AR-C"),  # second page of música
        ("tuentrada-virus-tgi", "concert", "AR-B"),  # Georef: province of Buenos Aires
    ]  # the tour is a group, "gone" redirects home, the Mendoza fest is dropped, sports are left out
    assert len(events) == 7
    georef = [url for url in site.requests if "/georef/api/ubicacion" in url]
    assert len(georef) == 3  # once per venue: Ituzaingó, Gran Rex (twice listed), Mendoza
    assert not any(url.endswith("/ntvg-gira") for url in site.requests)


def test_a_georef_failure_falls_back_to_the_city(monkeypatch):
    def answer(request: httpx.Request) -> httpx.Response:
        if request.url.host == "apis.datos.gob.ar":
            return httpx.Response(503, text="down")
        if request.url.path == "/busqueda":
            query = request.url.params
            entries = [{"slug": "luciano-pereyra-tgr", "model": "event"}]
            return httpx.Response(200, text=_listing_html(entries if "categoria" not in query or query["categoria"] == "música" else [], None))
        return httpx.Response(200, text=page("luciano_pereyra"))

    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    monkeypatch.setattr(tuentrada, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))
    events = scrape(delay=0, transport=httpx.MockTransport(answer))
    assert len(events) == 6 and {e.region for e in events} == {"AR-C"}


def test_a_listing_longer_than_expected_fails_instead_of_storing_part_of_it(monkeypatch):
    site = FakeTuEntrada(searches={"fechas": [[]] * (tuentrada.MAX_PAGES + 1)}, pages={}, provinces={})
    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    with pytest.raises(tuentrada.ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site))


def test_scrape_sends_our_user_agent(monkeypatch):
    agents: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        agents.append(request.headers["user-agent"])
        return httpx.Response(200, text=_listing_html([], None))

    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    assert scrape(delay=0, transport=httpx.MockTransport(answer)) == []
    assert set(agents) == {tuentrada.USER_AGENT}


def _one_show_site(slug: str, show_page: str, localities: dict[str, list[str]]) -> FakeTuEntrada:
    entry = [{"slug": slug, "model": "event"}]
    return FakeTuEntrada(searches={"fechas": [entry], "música": [entry]}, pages={slug: show_page}, provinces={}, localities=localities)


def test_a_venue_without_coordinates_is_placed_by_its_city_name(monkeypatch):
    site = _one_show_site("cgre-escobar", page("placeholder_map"), {"Belén De Escobar": ["Buenos Aires"]})
    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    monkeypatch.setattr(tuentrada, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))
    [e] = scrape(delay=0, transport=httpx.MockTransport(site))
    assert (e.title, e.venue, e.city, e.region) == ("Camila Gomez", "Teatro Seminari - Sala B", "Belén De Escobar", "AR-B")
    assert not any("/georef/api/ubicacion" in url for url in site.requests)  # the Obelisco is never asked about


def test_a_city_name_in_several_provinces_stays_unknown(monkeypatch):
    site = _one_show_site("cgre-escobar", page("placeholder_map"), {"Belén De Escobar": ["Buenos Aires", "Corrientes"]})
    monkeypatch.setattr(tuentrada.time, "sleep", lambda _s: None)
    monkeypatch.setattr(tuentrada, "datetime", type("Clock", (datetime,), {"now": classmethod(lambda cls, tz=None: NOW)}))
    assert scrape(delay=0, transport=httpx.MockTransport(site)) == []
    [all_regions] = [scrape(regions=None, delay=0, transport=httpx.MockTransport(site))]
    assert [(e.region, e.city) for e in all_regions] == [(None, "Belén De Escobar")]


def test_every_event_carries_its_venue_coordinates_and_none_when_the_page_has_only_the_map_placeholder():
    found = show("virus", "virus-tgi")
    assert found and {e.venue_point for e in found} == {(-34.66049613164969, -58.66711872545106)}
    placeholder = show("placeholder_map", "cgre-escobar")
    assert placeholder and {e.venue_point for e in placeholder} == {None}
