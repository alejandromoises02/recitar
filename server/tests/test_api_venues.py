import pytest
from fastapi.testclient import TestClient

from app.api.venues import upcoming_venues_source
from app.events_repository import VenueCount
from app.main import app


class FakeVenues:
    """Stands in for the database. The real count is covered in test_events_repository.py."""

    def __init__(self, venues: list[VenueCount]):
        self.venues, self.calls = venues, 0

    def __call__(self):
        self.calls += 1
        return self.venues


@pytest.fixture
def client_with():
    def make(venues: list[VenueCount]) -> TestClient:
        app.dependency_overrides[upcoming_venues_source] = lambda: FakeVenues(venues)
        return TestClient(app)

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
