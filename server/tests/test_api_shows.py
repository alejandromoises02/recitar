from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.shows import upcoming_shows_source
from app.domain.event import Show, ShowDateTickets, TicketLink
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def show(id_: str, hours: list[int], seen_days_ago: int = 0) -> Show:
    return Show(
        id=id_, category="concert", title=f"Show {id_}", name=f"Show {id_}", venue="Niceto Club", source_url=f"https://venti.live/{id_}",
        first_seen_at=NOW - timedelta(days=seen_days_ago),
        dates=[
            ShowDateTickets(
                id=f"{id_}-{h}", starts_at=NOW + timedelta(hours=h),
                ticket_links=[TicketLink(vendor="Venti", url=f"https://venti.live/{id_}/{h}")],
            )
            for h in hours
        ],
    )


class FakeShows:
    """Stands in for the database; the real grouping and keyset query are in test_shows_repository.py."""

    def __init__(self, items: list[Show]):
        self.items = items
        self.calls: list[dict] = []

    def __call__(self, limit, after, filters, sort):
        self.calls.append({"limit": limit, "after": after, "filters": filters, "sort": sort})
        if sort == "announced":
            ordered = sorted(self.items, key=lambda s: (s.first_seen_at, s.id), reverse=True)
            rest = [s for s in ordered if after is None or (s.first_seen_at, s.id) < after]
        else:
            ordered = sorted(self.items, key=lambda s: (s.dates[0].starts_at, s.id))
            rest = [s for s in ordered if after is None or (s.dates[0].starts_at, s.id) > after]
        return rest[:limit]


@pytest.fixture
def client_with():
    def make(items: list[Show]) -> tuple[TestClient, FakeShows]:
        fake = FakeShows(items)
        app.dependency_overrides[upcoming_shows_source] = lambda: fake
        return TestClient(app), fake

    yield make
    app.dependency_overrides.clear()


def ids(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def walk(client, **params) -> list[str]:
    seen, cursor = [], None
    while True:
        response = client.get("/shows", params={**params, **({"cursor": cursor} if cursor else {})})
        assert response.status_code == 200
        seen += ids(response)
        cursor = response.json()["next_cursor"]
        if cursor is None:
            return seen


def test_a_show_comes_with_every_date_and_its_ticket_links(client_with):
    client, _ = client_with([show("venti-x", [2, 30])])
    body = client.get("/shows").json()
    assert body["next_cursor"] is None
    (item,) = body["items"]
    assert item["id"] == "venti-x"
    assert [d["id"] for d in item["dates"]] == ["venti-x-2", "venti-x-30"]
    assert item["dates"][1]["ticket_links"] == [{"vendor": "Venti", "url": "https://venti.live/venti-x/30"}]
    assert item["dates"][0]["starts_at"].endswith("-03:00")  # Buenos Aires time, like /events
    assert datetime.fromisoformat(item["first_seen_at"]) == NOW


def test_shows_page_by_their_next_date_without_repeating_or_skipping(client_with):
    client, fake = client_with([show(f"s{i}", [5 - i, 50]) for i in range(5)])
    assert walk(client, limit=2) == ["s4", "s3", "s2", "s1", "s0"]
    assert fake.calls[0]["sort"] == "starts_at"


def test_sort_announced_pages_newest_first(client_with):
    client, _ = client_with([show(f"s{i}", [i + 1], seen_days_ago=i % 3) for i in range(5)])
    assert walk(client, limit=2, sort="announced") == ["s3", "s0", "s4", "s1", "s2"]


def test_the_filters_reach_the_source_like_in_events(client_with):
    client, fake = client_with([])
    params = {"q": " mila ", "from": "2026-11-14", "to": "2026-11-15", "venue": "Niceto Club",
              "category": "party", "announced_from": "2026-11-01"}
    assert client.get("/shows", params=params).status_code == 200
    filters = fake.calls[-1]["filters"]
    assert (filters.q, filters.venue, filters.category) == ("mila", "Niceto Club", "party")
    assert filters.starts_from == datetime(2026, 11, 14, 3, 0, tzinfo=timezone.utc)
    assert filters.starts_before == datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)
    assert filters.announced_from == datetime(2026, 11, 1, 3, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("first_sort,second_sort", [("starts_at", "announced"), ("announced", "starts_at")])
def test_a_cursor_only_works_with_the_sort_that_issued_it(client_with, first_sort, second_sort):
    client, _ = client_with([show(f"s{i}", [i + 1]) for i in range(3)])
    cursor = client.get("/shows", params={"sort": first_sort, "limit": 1}).json()["next_cursor"]
    response = client.get("/shows", params={"sort": second_sort, "cursor": cursor})
    assert (response.status_code, response.json()["title"]) == (400, "Invalid cursor")


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"sort": "title"}, {"category": "circus"},
                                    {"from": "mañana"}, {"from": "2026-11-20", "to": "2026-11-10"}])
def test_invalid_parameters_are_rejected_like_in_events(client_with, params):
    client, fake = client_with([])
    assert client.get("/shows", params=params).status_code == 422
    assert fake.calls == []


def test_no_shows_is_an_empty_page(client_with):
    client, _ = client_with([])
    assert client.get("/shows").json() == {"items": [], "next_cursor": None}


def test_the_endpoint_is_documented_with_the_same_parameters_as_events():
    paths = app.openapi()["paths"]
    names = lambda path: {p["name"] for p in paths[path]["get"]["parameters"]}  # noqa: E731
    assert names("/shows") == names("/events")
