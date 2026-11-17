import pytest
from fastapi.testclient import TestClient

from app.api.venues import upcoming_venues_source
from app.events_repository import VenueCount
from app.main import app


class FakeVenues:
    """Stands in for the database. The real count is covered in test_events_repository.py."""

    def __init__(self, venues: list[VenueCount]):
        self.venues, self.calls, self.categories = venues, 0, []

    def __call__(self, category=None):
        self.calls += 1
        self.categories.append(category)
        return self.venues


@pytest.fixture
def client_with():
    def make(venues: list[VenueCount]) -> TestClient:
        source = FakeVenues(venues)
        app.dependency_overrides[upcoming_venues_source] = lambda: source
        client = TestClient(app)
        client.source = source
        return client

    yield make
    app.dependency_overrides.clear()


def test_venues_come_with_their_number_of_upcoming_events_in_the_order_given(client_with):
    client = client_with([VenueCount(name="Niceto Club", upcoming_events=12), VenueCount(name="Teatro Colón", upcoming_events=44)])
    response = client.get("/venues")
    assert response.status_code == 200
    assert response.json() == {
        "items": [{"name": "Niceto Club", "upcoming_events": 12}, {"name": "Teatro Colón", "upcoming_events": 44}]
    }


def test_no_venues_is_an_empty_list(client_with):
    assert client_with([]).get("/venues").json() == {"items": []}


def test_the_venues_endpoint_is_documented_in_the_openapi_schema():
    schema = TestClient(app).get("/openapi.json").json()
    assert "get" in schema["paths"]["/venues"]
    assert "VenueList" in schema["components"]["schemas"]


def test_venues_can_count_one_kind_of_event_only(client_with):
    client = client_with([VenueCount(name="Niceto Club", upcoming_events=3)])
    assert client.get("/venues", params={"category": "concert"}).status_code == 200
    assert client.source.categories == ["concert"]


def test_without_a_category_venues_count_every_kind_as_before(client_with):
    client = client_with([])
    client.get("/venues")
    assert client.source.categories == [None]


def test_an_unknown_category_for_venues_is_refused(client_with):
    assert client_with([]).get("/venues", params={"category": "opera"}).status_code == 422
