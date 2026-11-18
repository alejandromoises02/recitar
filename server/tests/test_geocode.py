import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import text

from app.domain.event import VENUE_TO_BE_CONFIRMED, Event, TicketLink
from app.events_repository import upsert_events
from app.geocode import NOMINATIM_URL, geocode_venues, pick_place

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)


def results(name: str) -> list[dict]:
    return json.loads((FIXTURES / f"nominatim_{name}.json").read_text(encoding="utf-8"))


def test_the_first_place_in_the_venue_region_is_picked_with_its_street_address():
    place = pick_place(results("niceto"), "AR-C")
    assert place is not None
    assert (place.latitude, place.longitude, place.address) == (-34.5874108, -58.4389128, "Avenida Coronel Niceto Vega 5510")


def test_a_place_in_another_province_is_skipped():
    # The first four results are clubs in Buenos Aires province; ours is in the city.
    place = pick_place(results("club_ciudad"), "AR-C")
    assert place is not None
    assert (place.latitude, place.longitude) == (-34.5420036, -58.4578306)


def test_bus_stops_streets_and_towns_are_not_places():
    place = pick_place(results("hipodromo"), "AR-C")  # two bus stops called Hipódromo come first
    assert place is not None
    assert (place.latitude, place.longitude, place.address) == (-34.5663978, -58.4257272, "Avenida Del Libertador 4101")


def test_nothing_found_is_no_place():
    assert pick_place(results("not_found"), "AR-C") is None
    assert pick_place(results("niceto"), "AR-B") is None


def _event(id_: str, venue: str, region: str | None = "AR-C", city: str | None = "Buenos Aires", **extra) -> Event:
    return Event(
        id=id_, category="concert", title="A", venue=venue, city=city, region=region, country="AR",
        starts_at=NOW + timedelta(days=5), ticket_links=[TicketLink(vendor="X", url="https://x")],
        source_url="https://x", updated_at=NOW, **extra,
    )


class FakeNominatim:
    def __init__(self, answers: dict[str, httpx.Response]):
        self.answers = answers
        self.queries: list[dict[str, str]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(NOMINATIM_URL)
        params = dict(request.url.params)
        self.queries.append(params)
        return self.answers.get(params["q"], httpx.Response(200, json=[]))


def _row(conn, name: str):
    return tuple(conn.execute(text(
        "SELECT latitude, longitude, address, coords_source FROM venues WHERE name = :name"
    ), {"name": name}).one())


def test_venues_without_coordinates_are_geocoded_one_by_one_and_a_failure_does_not_stop_the_rest(db_engine):
    fake = FakeNominatim({
        "Niceto Club, Buenos Aires, Argentina": httpx.Response(200, json=results("niceto")),
        "Club Ciudad, Buenos Aires, Argentina": httpx.Response(500),
        "Hipódromo de Palermo, Buenos Aires, Argentina": httpx.Response(200, json=results("hipodromo")),
    })
    sleeps: list[float] = []
    with db_engine.begin() as conn:
        upsert_events(conn, [
            _event("a-1-20261123T2100", "Niceto Club"),
            _event("a-2-20261123T2100", "Club Ciudad"),
            _event("a-3-20261123T2100", "Hipódromo de Palermo"),
            _event("a-4-20261123T2100", "Movistar Arena", venue_point=(-34.59, -58.45)),  # already placed
            _event("a-5-20261123T2100", VENUE_TO_BE_CONFIRMED),
            _event("a-6-20261123T2100", "Sala Sin Provincia", region=None, city=None),
            _event("a-7-20261123T2100", "Corrected By Hand"),
        ])
        conn.execute(text("UPDATE venues SET coords_source = 'manual' WHERE name = 'Corrected By Hand'"))
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            report = geocode_venues(conn, client, delay=1.0, sleep=sleeps.append)
        assert _row(conn, "Niceto Club") == (-34.5874108, -58.4389128, "Avenida Coronel Niceto Vega 5510", "osm")
        assert _row(conn, "Hipódromo de Palermo") == (-34.5663978, -58.4257272, "Avenida Del Libertador 4101", "osm")
        assert _row(conn, "Club Ciudad") == (None, None, None, None)
        assert _row(conn, "Movistar Arena") == (-34.59, -58.45, None, "ticketer")
        assert _row(conn, VENUE_TO_BE_CONFIRMED) == (None, None, None, None)
        assert _row(conn, "Sala Sin Provincia") == (None, None, None, None)
        assert _row(conn, "Corrected By Hand") == (None, None, None, "manual")
    assert [q["q"] for q in fake.queries] == [
        "Club Ciudad, Buenos Aires, Argentina",
        "Hipódromo de Palermo, Buenos Aires, Argentina",
        "Niceto Club, Buenos Aires, Argentina",
    ]
    assert {(q["format"], q["addressdetails"], q["limit"], q["countrycodes"]) for q in fake.queries} == {("jsonv2", "1", "5", "ar")}
    assert sleeps == [1.0, 1.0, 1.0]  # Nominatim allows one request per second
    assert report.found == ["Hipódromo de Palermo", "Niceto Club"]
    assert report.missed == []
    assert list(report.failed) == ["Club Ciudad"]


def test_a_venue_nominatim_does_not_know_is_reported_as_missed(db_engine):
    fake = FakeNominatim({})
    with db_engine.begin() as conn:
        upsert_events(conn, [_event("a-1-20261123T2100", "Sala Inventada Zzyx")])
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            report = geocode_venues(conn, client, delay=0, sleep=lambda _s: None)
        assert _row(conn, "Sala Inventada Zzyx") == (None, None, None, None)
    assert (report.found, report.missed, dict(report.failed)) == ([], ["Sala Inventada Zzyx"], {})


def test_the_city_most_events_give_is_used_and_a_venue_without_city_is_asked_with_its_name_only(db_engine):
    fake = FakeNominatim({})
    with db_engine.begin() as conn:
        upsert_events(conn, [
            _event("a-1-20261123T2100", "Teatro Ópera", city="La Plata", region="AR-B"),
            _event("a-2-20261124T2100", "Teatro Ópera", city="La Plata", region="AR-B"),
            _event("a-3-20261125T2100", "Teatro Ópera", city="Tolosa", region="AR-B"),
            _event("a-4-20261123T2100", "Estadio Único", city=None, region="AR-B"),
        ])
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            geocode_venues(conn, client, delay=0, sleep=lambda _s: None)
    assert [q["q"] for q in fake.queries] == ["Estadio Único, Argentina", "Teatro Ópera, La Plata, Argentina"]
