from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.events import upcoming_events_source
from app.domain.event import Event, TicketLink
from app.events_repository import EventFilters
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def event(id_: str, hours: int) -> Event:
    return Event(
        id=id_, category="concert", title=f"Show {id_}", venue="Niceto Club", starts_at=NOW + timedelta(hours=hours),
        ticket_links=[TicketLink(vendor="Venti", url=f"https://venti.live/{id_}")],
        source_url=f"https://venti.live/{id_}", updated_at=NOW,
    )


class FakeEvents:
    """Stands in for the database. The real keyset query is covered in test_events_repository.py."""

    def __init__(self, events: list[Event]):
        self.events = sorted(events, key=lambda e: (e.starts_at, e.id))
        self.calls: list[dict] = []

    def __call__(self, limit, after, filters):
        self.calls.append({"limit": limit, "after": after, "filters": filters})
        rest = [e for e in self.events if after is None or (e.starts_at, e.id) > after]
        return rest[:limit]


@pytest.fixture
def client_with():
    def make(events: list[Event]) -> tuple[TestClient, FakeEvents]:
        fake = FakeEvents(events)
        app.dependency_overrides[upcoming_events_source] = lambda: fake
        return TestClient(app), fake

    yield make
    app.dependency_overrides.clear()


def ids(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def test_a_page_has_the_items_and_a_cursor_to_the_next_one(client_with):
    client, _ = client_with([event(f"e{i}", i) for i in range(3)])
    response = client.get("/events", params={"limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "next_cursor"}
    assert ids(response) == ["e0", "e1"]
    assert body["items"][0]["title"] == "Show e0"
    assert isinstance(body["next_cursor"], str)


def test_following_the_cursor_gives_the_rest_without_repeating_or_skipping(client_with):
    client, _ = client_with([event(f"e{i}", i) for i in range(5)])
    seen, cursor = [], None
    while True:
        response = client.get("/events", params={"limit": 2, **({"cursor": cursor} if cursor else {})})
        seen += ids(response)
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    assert seen == ["e0", "e1", "e2", "e3", "e4"]


def test_events_at_the_same_time_are_ordered_by_id_and_none_is_lost_between_pages(client_with):
    client, _ = client_with([event("b", 1), event("a", 1), event("c", 1)])
    first = client.get("/events", params={"limit": 2})
    second = client.get("/events", params={"limit": 2, "cursor": first.json()["next_cursor"]})
    assert ids(first) + ids(second) == ["a", "b", "c"]


def test_the_last_page_has_no_cursor(client_with):
    client, _ = client_with([event("e0", 0), event("e1", 1)])
    response = client.get("/events", params={"limit": 2})
    assert ids(response) == ["e0", "e1"]
    assert response.json()["next_cursor"] is None


def test_no_events_is_an_empty_page(client_with):
    client, _ = client_with([])
    assert client.get("/events").json() == {"items": [], "next_cursor": None}


def test_the_default_limit_is_20(client_with):
    client, fake = client_with([event(f"e{i:02}", i) for i in range(25)])
    assert len(ids(client.get("/events"))) == 20
    assert fake.calls[-1]["limit"] == 21  # one extra row tells whether there is a next page


@pytest.mark.parametrize("limit", [0, 101, -1])
def test_a_limit_outside_1_to_100_is_rejected(client_with, limit):
    client, fake = client_with([event("e0", 0)])
    response = client.get("/events", params={"limit": limit})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 422
    assert fake.calls == []


def test_100_is_the_largest_limit_accepted(client_with):
    client, fake = client_with([event("e0", 0)])
    assert client.get("/events", params={"limit": 100}).status_code == 200
    assert fake.calls[-1]["limit"] == 101


@pytest.mark.parametrize("cursor", ["not-a-cursor", "e30=", "eyJ4IjogMX0"])
def test_a_cursor_we_did_not_issue_is_a_bad_request(client_with, cursor):
    client, fake = client_with([event("e0", 0)])
    response = client.get("/events", params={"cursor": cursor})
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert (body["status"], body["title"]) == (400, "Invalid cursor")
    assert "first page" in body["detail"]
    assert fake.calls == []


def test_the_endpoint_is_documented_in_the_openapi_schema():
    schema = TestClient(app).get("/openapi.json").json()
    operation = schema["paths"]["/events"]["get"]
    assert {p["name"] for p in operation["parameters"]} == {"cursor", "limit", "q"}
    assert "EventPage" in schema["components"]["schemas"]


def test_health_still_answers():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_q_is_passed_to_the_search_trimmed(client_with):
    client, fake = client_with([event("e0", 0)])
    assert client.get("/events", params={"q": "  maria becerra "}).status_code == 200
    assert fake.calls[-1]["filters"] == EventFilters(q="maria becerra")


@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "   "}])
def test_without_a_search_every_upcoming_event_is_listed(client_with, params):
    client, fake = client_with([event("e0", 0)])
    assert ids(client.get("/events", params=params)) == ["e0"]
    assert fake.calls[-1]["filters"] == EventFilters(q=None)


def test_a_search_longer_than_100_characters_is_rejected(client_with):
    client, fake = client_with([event("e0", 0)])
    response = client.get("/events", params={"q": "a" * 101})
    assert response.status_code == 422
    assert response.json()["errors"][0]["loc"] == ["query", "q"]
    assert fake.calls == []
    assert client.get("/events", params={"q": "a" * 100}).status_code == 200
