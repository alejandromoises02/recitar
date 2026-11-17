"""Ticketek: the search API (an empty query, page by page) lists the shows; each show's node API holds its
schema.org MusicEvent entries, one per performance. Fixtures are real answers captured 2026-11-16."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.scrapers import ticketek
from app.scrapers.ticketek import artist_show_paths, listing_page, listing_url, node_url, parse_show, region_of, scrape

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 16, 12, 0, tzinfo=BA)


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"ticketek_{name}.json").read_text(encoding="utf-8"))


def show(name: str, path: str, now: datetime = NOW):
    return parse_show(fixture(name), path, now)


def test_a_concert_has_its_date_venue_city_and_official_page():
    [e] = show("tarja", "tarja/teatro-coliseo")
    assert e.id == "ticketek-tarja-teatro-coliseo-20261201T2100"
    assert (e.title, e.artist, e.category) == ("Tarja", "Tarja", "concert")
    assert e.starts_at.isoformat() == "2026-12-01T21:00:00-03:00" and e.time_known
    assert (e.venue, e.city, e.region, e.country) == ("Teatro Coliseo", "Buenos Aires", "AR-C", "AR")
    assert e.ticket_links[0].model_dump() == {"vendor": "Ticketek", "url": "https://www.ticketek.com.ar/tarja/teatro-coliseo"}
    assert e.source_url == "https://www.ticketek.com.ar/tarja/teatro-coliseo"
    assert e.image_url.startswith("https://prod-cms-static.ticketek.com.ar/") and e.image_origin == "source"


def test_every_performance_is_its_own_date_and_past_ones_are_dropped():
    starts = [e.starts_at.isoformat() for e in show("theatre", "campo-minado/teatro-coliseo")]
    assert len(starts) == 9 and starts[-1] == "2026-11-29T20:00:00-03:00"
    later = [e.starts_at for e in show("theatre", "campo-minado/teatro-coliseo", now=datetime(2026, 11, 28, 12, tzinfo=BA))]
    assert [d.isoformat() for d in later] == ["2026-11-28T20:00:00-03:00", "2026-11-29T20:00:00-03:00"]


def test_bundles_that_are_not_performances_do_not_become_dates():
    # The festival sells day tickets and passes; only the two days are MusicEvents.
    starts = [e.starts_at.isoformat() for e in show("bundles", "festival-isoca/club-s-d-villa-del-parque")]
    assert starts == ["2027-02-13T10:00:00-03:00", "2027-02-14T10:00:00-03:00"]


def test_theatre_is_theatre_and_has_no_artist():
    e = show("theatre", "campo-minado/teatro-coliseo")[0]
    assert (e.category, e.artist) == ("theatre", None)


def test_specials_are_theatre():
    assert show("barrio", "la-gala-enchantee/palacio-de-la-reconquista")[0].category == "theatre"


@pytest.mark.parametrize("ticketek_category, category", [
    ("Musica", "concert"), ("Internacionales", "concert"), ("Teatro", "theatre"),
    ("Especiales", "theatre"), ("Familia", "theatre"), ("Una categoría nueva", "other"),
])
def test_each_ticketek_category_maps_to_ours(ticketek_category, category):
    node = fixture("tarja") | {"category": {"parent": ticketek_category, "childs": ""}}
    [e] = parse_show(node, "tarja/teatro-coliseo", NOW)
    assert e.category == category
    assert e.artist == ("Tarja" if category == "concert" else None)


def test_a_party_listed_under_music_is_other():
    [party] = show("fiesta", "fiesta-fa/bendu-arena")
    assert party.category == "other"  # "Fiesta Fa!" is listed under Música


def test_a_tribute_listed_under_music_is_a_tribute():
    node = fixture("tarja") | {"title": "Katseye: The tribute experience"}
    [e] = parse_show(node, "tarja/teatro-coliseo", NOW)
    assert (e.category, e.artist) == ("tribute", None)


def test_sports_are_left_out():
    assert show("polo", "triple-corona/campo-argentino-de-polo") == []


def test_a_canceled_show_gives_nothing_though_its_date_is_still_published():
    node = fixture("canceled")
    assert node["google_structured_data"][0]["startDate"] == "2026-11-26T21:00:00-03:00"
    assert show("canceled", "sueno-de-pescado/teatro-opera") == []


def test_a_page_without_performances_gives_nothing():
    assert show("no_dates", "casa-de-la-cultura/casa-de-la-cultura-ex-edificio-la-prensa") == []


def test_city_neighbourhoods_filed_under_the_province_are_the_city():
    e = show("barrio", "la-gala-enchantee/palacio-de-la-reconquista")[0]
    assert (e.region, e.city) == ("AR-C", "Buenos Aires")


def test_the_province_stays_the_province():
    [e] = show("dillom_mdp", "dillom/bendu-arena")
    assert (e.region, e.city) == ("AR-B", "Mar del Plata")


@pytest.mark.parametrize("state, city, region", [
    ("Capital Federal", "Centro", "AR-C"),
    ("Capital Federal", "Belgrano", "AR-C"),
    ("Buenos Aires", "CABA", "AR-C"),
    ("Buenos Aires", "Ciudad Autonoma de Buenos Aires", "AR-C"),
    ("Buenos Aires", "Palermo", "AR-C"),
    ("Buenos Aires", "Microcentro", "AR-C"),
    ("Buenos Aires", "Barrio San Nicolas", "AR-C"),
    ("Buenos Aires", "Villa Devoto", "AR-C"),
    ("Buenos Aires", "San Nicolas", "AR-B"),  # also a city of the province: only "Barrio San Nicolás" is the city's
    ("Buenos Aires", "Mar del Plata", "AR-B"),
    ("Buenos Aires", "San Justo", "AR-B"),
    ("Mendoza", "Maipu", "AR-M"),
    ("", "", None),
])
def test_region_of(state, city, region):
    assert region_of(state, city) == region


def test_artist_pages_point_to_their_shows():
    assert artist_show_paths(fixture("artist_abel_pintos")) == ["abel-pintos/arena-maipu", "abel-pintos/estadio-san-nicolas"]


def test_a_listing_page_gives_its_show_paths_and_the_next_page():
    # Real pages of the empty query: the first one is empty but still points to the next.
    assert listing_page(fixture("search_first")) == ([], "search/ ?pagina=1")
    assert listing_page(fixture("search_middle")) == (["tarja/teatro-coliseo"], "search/ ?pagina=2")
    paths, following = listing_page(fixture("search_last"))
    assert "juli-bellese" in paths and len(paths) == 8 and following is None


def test_the_next_page_is_encoded_as_the_site_sends_it():
    assert listing_url("search/ ?pagina=1") == "https://prod-cms-search.ticketek.com.ar/api/1.1/search/%20?pagina=1"
    assert listing_url(ticketek.LISTING_START) == "https://prod-cms-search.ticketek.com.ar/api/1.1/search/%20"


def test_node_url_is_built_like_the_site_builds_it():
    assert node_url("tarja/teatro-coliseo") == "https://prod-cms-api.ticketek.com.ar/api/1.0/node%3Fpath%3Dtarja--teatro-coliseo"
    assert node_url("hairspray") == "https://prod-cms-api.ticketek.com.ar/api/1.0/node%3Fpath%3Dhairspray"


class FakeTicketek:
    """Serves listing pages in order (each pointing to the next, as the site does) and nodes by path."""

    def __init__(self, pages: list[list[str]], nodes: dict[str, dict]):
        self.pages, self.nodes, self.listing_requests = pages, nodes, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "prod-cms-search.ticketek.com.ar":
            self.listing_requests.append(request.url.raw_path.decode())
            raw = request.url.raw_path.decode()
            index = int(raw.rsplit("pagina=", 1)[1]) if "pagina=" in raw else 0
            following = f"search/ ?pagina={index + 1}" if index + 1 < len(self.pages) else None
            body = {"resultados": [{"url": path} for path in self.pages[index]]}
            return httpx.Response(200, json=body | ({"siguiente": following} if following else {}))
        key = request.url.raw_path.decode().split("path%3D", 1)[1]
        node = self.nodes.get(key)
        return httpx.Response(200, content=json.dumps(node).encode()) if node else httpx.Response(404, text="Not Found")


def test_scrape_walks_every_page_even_empty_ones_follows_artist_pages_and_keeps_buenos_aires(monkeypatch):
    mendoza = fixture("dillom_mdp") | {"venue": {**fixture("dillom_mdp")["venue"], "state": "Mendoza", "city": "Maipu"}}
    site = FakeTicketek(
        pages=[[], ["tarja/teatro-coliseo"], ["abel-pintos", "tarja/teatro-coliseo"]],
        nodes={
            "tarja--teatro-coliseo": fixture("tarja"),
            "abel-pintos": fixture("artist_abel_pintos"),  # points to arena-maipu and estadio-san-nicolas
            "abel-pintos--arena-maipu": mendoza,
            "abel-pintos--estadio-san-nicolas": fixture("dillom_mdp"),
        },
    )
    monkeypatch.setattr(ticketek.time, "sleep", lambda _s: None)
    events = scrape(delay=0, transport=httpx.MockTransport(site))
    assert sorted(e.id for e in events) == [
        "ticketek-abel-pintos-estadio-san-nicolas-20270130T2100",  # province, kept
        "ticketek-tarja-teatro-coliseo-20261201T2100",  # listed twice, read once
    ]  # the Mendoza show is dropped
    assert site.listing_requests == ["/api/1.1/search/%20", "/api/1.1/search/%20?pagina=1", "/api/1.1/search/%20?pagina=2"]


def test_a_listing_longer_than_expected_fails_instead_of_storing_part_of_it(monkeypatch):
    site = FakeTicketek(pages=[[]] * (ticketek.MAX_PAGES + 1), nodes={})
    monkeypatch.setattr(ticketek.time, "sleep", lambda _s: None)
    with pytest.raises(ticketek.ListingTooLongError):
        scrape(delay=0, transport=httpx.MockTransport(site))


def test_scrape_sends_our_user_agent(monkeypatch):
    agents: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        agents.append(request.headers["user-agent"])
        return httpx.Response(200, json={"resultados": []})

    monkeypatch.setattr(ticketek.time, "sleep", lambda _s: None)
    assert scrape(delay=0, transport=httpx.MockTransport(answer)) == []
    assert set(agents) == {ticketek.USER_AGENT}
