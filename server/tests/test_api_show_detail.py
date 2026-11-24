from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.shows import show_detail_source
from app.domain.event import Event, Show, ShowDetail, TicketLink, VenueLocation
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def date(id_: str, days: int, read_hours_ago: int, **extra) -> Event:
    return Event(
        id=id_, category="concert", title="María Becerra", venue="Movistar Arena", starts_at=NOW + timedelta(days=days),
        ticket_links=[TicketLink(vendor="Movistar Arena", url=f"https://tickets.example/{id_}")],
        source_url="https://www.movistararena.com.ar/show/x", updated_at=NOW - timedelta(hours=read_hours_ago),
        first_seen_at=NOW - timedelta(days=3), **extra,
    )


SHOW = Show.from_dates(
    "movistar-becerra",
    [date("movistar-becerra-20261115T2100", 6, read_hours_ago=5), date("movistar-becerra-20261117T2100", 8, read_hours_ago=2)],
    NOW - timedelta(days=3),
)

DETAIL = ShowDetail(**SHOW.model_dump(), venue_location=None)


class FakeShow:
    def __init__(self, stored: dict[str, Show]):
        self.stored, self.calls = stored, []

    def __call__(self, show_id):
        self.calls.append(show_id)
        return self.stored.get(show_id)


@pytest.fixture
def client_with():
    def make(stored: dict[str, Show]) -> tuple[TestClient, FakeShow]:
        fake = FakeShow(stored)
        app.dependency_overrides[show_detail_source] = lambda: fake
        return TestClient(app), fake

    yield make
    app.dependency_overrides.clear()


def test_a_show_comes_with_every_upcoming_date_its_ticket_links_and_when_it_was_read(client_with):
    client, fake = client_with({DETAIL.id: DETAIL})
    response = client.get("/shows/movistar-becerra")
    assert response.status_code == 200
    body = response.json()
    assert fake.calls == ["movistar-becerra"]
    assert (body["id"], body["name"], body["venue"]) == ("movistar-becerra", "María Becerra", "Movistar Arena")
    assert [d["id"] for d in body["dates"]] == ["movistar-becerra-20261115T2100", "movistar-becerra-20261117T2100"]
    assert body["dates"][1]["ticket_links"] == [{"vendor": "Movistar Arena", "url": "https://tickets.example/movistar-becerra-20261117T2100"}]
    assert datetime.fromisoformat(body["updated_at"]) == NOW - timedelta(hours=2)


def test_an_unknown_show_is_a_404_problem(client_with):
    client, fake = client_with({})
    response = client.get("/shows/movistar-nobody")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert (body["status"], body["title"]) == (404, "Show not found")
    assert "movistar-nobody" in body["detail"]
    assert fake.calls == ["movistar-nobody"]


def test_the_list_still_answers_at_shows(client_with):
    from app.api.shows import upcoming_shows_source

    app.dependency_overrides[upcoming_shows_source] = lambda: (lambda limit, after, filters, sort: [SHOW])
    client, _ = client_with({})
    assert [item["id"] for item in client.get("/shows").json()["items"]] == ["movistar-becerra"]


def test_the_show_endpoint_is_documented_with_its_404():
    schema = TestClient(app).get("/openapi.json").json()
    responses = schema["paths"]["/shows/{show_id}"]["get"]["responses"]
    assert set(responses) >= {"200", "404"}


def test_the_show_says_where_its_venue_is(client_with):
    placed = ShowDetail(**SHOW.model_dump(), venue_location=VenueLocation(
        address="Humboldt 450", latitude=-34.5937, longitude=-58.4476,
    ))
    client, _ = client_with({placed.id: placed})
    body = client.get("/shows/movistar-becerra").json()
    assert body["venue_location"] == {"address": "Humboldt 450", "latitude": -34.5937, "longitude": -58.4476}


def test_a_venue_without_coordinates_has_a_null_location(client_with):
    client, _ = client_with({DETAIL.id: DETAIL})
    body = client.get("/shows/movistar-becerra").json()
    assert "venue_location" in body and body["venue_location"] is None


def test_the_list_does_not_carry_the_venue_location(client_with):
    from app.api.shows import upcoming_shows_source

    app.dependency_overrides[upcoming_shows_source] = lambda: (lambda limit, after, filters, sort: [SHOW])
    [item] = TestClient(app).get("/shows").json()["items"]
    assert "venue_location" not in item


def test_the_show_carries_its_artist_spotify_id(client_with):
    found = ShowDetail(**{**SHOW.model_dump(), "spotify_artist_id": "67oZkRi3cta1wNxN3KoFt5"}, venue_location=None)
    client, _ = client_with({found.id: found})
    body = client.get("/shows/movistar-becerra").json()
    assert body["spotify_artist_id"] == "67oZkRi3cta1wNxN3KoFt5"


def test_an_artist_not_found_on_spotify_has_a_null_id(client_with):
    client, _ = client_with({DETAIL.id: DETAIL})
    body = client.get("/shows/movistar-becerra").json()
    assert "spotify_artist_id" in body and body["spotify_artist_id"] is None


def test_the_list_carries_the_spotify_id_too_for_the_featured_record_player(client_with):
    from app.api.shows import upcoming_shows_source

    on_spotify = SHOW.model_copy(update={"spotify_artist_id": "67oZkRi3cta1wNxN3KoFt5"})
    app.dependency_overrides[upcoming_shows_source] = lambda: (lambda limit, after, filters, sort: [on_spotify, SHOW])
    items = TestClient(app).get("/shows").json()["items"]
    assert [item["spotify_artist_id"] for item in items] == ["67oZkRi3cta1wNxN3KoFt5", None]
