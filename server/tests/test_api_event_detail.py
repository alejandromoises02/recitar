from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.events import event_detail_source
from app.domain.event import Event, ShowDate, TicketLink, show_key
from app.main import app

UTC = timezone.utc
NOW = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


def event(id_: str, when: datetime, **extra) -> Event:
    return Event(
        id=id_, category="theatre", title="El Cascanueces", venue="Teatro Colón", starts_at=when,
        ticket_links=[TicketLink(vendor="Entradas BA", url="https://entradas.example/1")],
        source_url="https://teatrocolon.org.ar/x", updated_at=NOW, **extra,
    )


SHOW = event(
    "colon-el-cascanueces-20261118T2000", datetime(2026, 11, 18, 23, 0, tzinfo=UTC),
    image_url="/media/abc.webp", image_origin="licensed", image_author="Ana", image_license="CC BY 4.0",
    image_source_url="https://commons.wikimedia.org/wiki/File:X.jpg",
)
OTHER = ShowDate(id="colon-el-cascanueces-20261120T2000", starts_at=datetime(2026, 11, 20, 23, 0, tzinfo=UTC))


class FakeDetails:
    def __init__(self, stored: dict[str, Event], dates: dict[str, list[ShowDate]]):
        self.stored, self.dates, self.calls = stored, dates, []

    def __call__(self, event_id):
        self.calls.append(event_id)
        found = self.stored.get(event_id)
        return None if found is None else (found, self.dates.get(show_key(event_id), []))


@pytest.fixture
def client_with():
    def make(stored: dict[str, Event], dates: dict[str, list[ShowDate]] | None = None):
        fake = FakeDetails(stored, dates or {})
        app.dependency_overrides[event_detail_source] = lambda: fake
        return TestClient(app), fake

    yield make
    app.dependency_overrides.clear()


def test_the_show_key_is_the_id_without_its_date():
    assert show_key("colon-el-cascanueces-2-20261119T2000") == "colon-el-cascanueces-2"
    assert show_key("movistar-993a2d46-39d7-4455-b199-87a5a2dc9b83-20261120T2100") == (
        "movistar-993a2d46-39d7-4455-b199-87a5a2dc9b83"
    )


def test_an_event_comes_with_every_field_and_the_other_dates_of_its_show(client_with):
    same_date = ShowDate(id=SHOW.id, starts_at=SHOW.starts_at)
    client, _ = client_with({SHOW.id: SHOW}, {"colon-el-cascanueces": [same_date, OTHER]})
    response = client.get(f"/events/{SHOW.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == SHOW.id
    assert body["ticket_links"] == [{"vendor": "Entradas BA", "url": "https://entradas.example/1"}]
    assert (body["image_author"], body["image_license"]) == ("Ana", "CC BY 4.0")
    assert body["source_url"] == "https://teatrocolon.org.ar/x"
    assert body["starts_at"] == "2026-11-18T20:00:00-03:00"
    # the event itself is not repeated among its other dates; times read in Buenos Aires
    assert body["other_dates"] == [{"id": OTHER.id, "starts_at": "2026-11-20T20:00:00-03:00"}]


def test_a_show_with_one_date_has_no_other_dates(client_with):
    client, _ = client_with({SHOW.id: SHOW})
    assert client.get(f"/events/{SHOW.id}").json()["other_dates"] == []


def test_a_past_event_is_still_found(client_with):
    past = event("colon-el-cascanueces-20261101T2000", NOW - timedelta(days=8))
    client, _ = client_with({past.id: past}, {"colon-el-cascanueces": [OTHER]})
    body = client.get(f"/events/{past.id}").json()
    assert body["id"] == past.id
    assert [d["id"] for d in body["other_dates"]] == [OTHER.id]


def test_an_unknown_event_is_a_404_problem(client_with):
    client, fake = client_with({})
    response = client.get("/events/colon-nope-20261118T2000")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert (body["status"], body["title"]) == (404, "Event not found")
    assert "colon-nope-20261118T2000" in body["detail"]
    assert fake.calls == ["colon-nope-20261118T2000"]


def test_the_detail_endpoint_is_documented():
    schema = TestClient(app).get("/openapi.json").json()
    assert "404" in schema["paths"]["/events/{event_id}"]["get"]["responses"]
    assert "EventDetail" in schema["components"]["schemas"]


def test_the_list_still_answers_at_events(client_with):
    from app.api.events import upcoming_events_source

    app.dependency_overrides[upcoming_events_source] = lambda: (lambda limit, after, filters: [])
    assert TestClient(app).get("/events").json() == {"items": [], "next_cursor": None}
