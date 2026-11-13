from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.events import upcoming_events_source
from app.domain.event import Event, TicketLink
from app.events_repository import EventFilters
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def event(id_: str, hours: int, seen_days_ago: int = 0) -> Event:
    return Event(
        id=id_, category="concert", title=f"Show {id_}", venue="Niceto Club", starts_at=NOW + timedelta(hours=hours),
        ticket_links=[TicketLink(vendor="Venti", url=f"https://venti.live/{id_}")],
        source_url=f"https://venti.live/{id_}", updated_at=NOW, first_seen_at=NOW - timedelta(days=seen_days_ago),
    )


class FakeEvents:
    """Stands in for the database. The real keyset query is covered in test_events_repository.py."""

    def __init__(self, events: list[Event]):
        self.events = events
        self.calls: list[dict] = []

    def __call__(self, limit, after, filters, sort="starts_at"):
        self.calls.append({"limit": limit, "after": after, "filters": filters, "sort": sort})
        if sort == "announced":  # newest first; ties by id, also descending
            ordered = sorted(self.events, key=lambda e: (e.first_seen_at, e.id), reverse=True)
            follows = lambda e: after is None or (e.first_seen_at, e.id) < after  # noqa: E731
        else:
            ordered = sorted(self.events, key=lambda e: (e.starts_at, e.id))
            follows = lambda e: after is None or (e.starts_at, e.id) > after  # noqa: E731
        rest = [
            e for e in ordered
            if follows(e)
            and (filters.announced_from is None or e.first_seen_at >= filters.announced_from)
            and (filters.starts_from is None or e.starts_at >= filters.starts_from)
            and (filters.starts_before is None or e.starts_at < filters.starts_before)
            and (filters.venue is None or e.venue == filters.venue)
            and (filters.category is None or e.category == filters.category)
        ]
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
    assert {p["name"] for p in operation["parameters"]} == {"cursor", "limit", "q", "from", "to", "venue", "category", "sort", "announced_from"}
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


UTC = timezone.utc


def at(id_: str, when: datetime) -> Event:
    return event(id_, 0).model_copy(update={"starts_at": when})


# Saturday 2026-11-14 in Buenos Aires (UTC-3) runs from 03:00 UTC on the 14th to 03:00 UTC on the 15th.
SATURDAY_NIGHT = at("sat-22h", datetime(2026, 11, 15, 1, 0, tzinfo=UTC))  # Saturday 22:00 in Buenos Aires
SATURDAY_LAST_MINUTE = at("sat-23h59", datetime(2026, 11, 15, 2, 59, tzinfo=UTC))  # Saturday 23:59
SUNDAY_MIDNIGHT = at("sun-00h00", datetime(2026, 11, 15, 3, 0, tzinfo=UTC))  # Sunday 00:00
FRIDAY_LATE = at("fri-23h30", datetime(2026, 11, 14, 2, 30, tzinfo=UTC))  # Friday 23:30
NIGHT = [FRIDAY_LATE, SATURDAY_NIGHT, SATURDAY_LAST_MINUTE, SUNDAY_MIDNIGHT]


def test_a_day_is_the_buenos_aires_day_not_the_utc_one(client_with):
    client, fake = client_with(NIGHT)
    response = client.get("/events", params={"from": "2026-11-14", "to": "2026-11-14"})
    assert ids(response) == ["sat-22h", "sat-23h59"]
    filters = fake.calls[-1]["filters"]
    assert filters.starts_from == datetime(2026, 11, 14, 3, 0, tzinfo=UTC)
    assert filters.starts_before == datetime(2026, 11, 15, 3, 0, tzinfo=UTC)


def test_a_show_at_midnight_belongs_to_the_day_that_starts(client_with):
    client, _ = client_with(NIGHT)
    assert ids(client.get("/events", params={"from": "2026-11-15", "to": "2026-11-15"})) == ["sun-00h00"]
    assert ids(client.get("/events", params={"from": "2026-11-13", "to": "2026-11-13"})) == ["fri-23h30"]


def test_a_range_includes_both_days(client_with):
    client, _ = client_with(NIGHT)
    response = client.get("/events", params={"from": "2026-11-13", "to": "2026-11-14"})
    assert ids(response) == ["fri-23h30", "sat-22h", "sat-23h59"]


def test_only_from_means_from_that_day_on(client_with):
    client, fake = client_with(NIGHT)
    assert ids(client.get("/events", params={"from": "2026-11-14"})) == ["sat-22h", "sat-23h59", "sun-00h00"]
    assert fake.calls[-1]["filters"].starts_before is None


def test_only_to_means_until_the_end_of_that_day(client_with):
    client, fake = client_with(NIGHT)
    assert ids(client.get("/events", params={"to": "2026-11-13"})) == ["fri-23h30"]
    assert fake.calls[-1]["filters"].starts_from is None


def test_dates_combine_with_the_search_and_page_with_the_cursor(client_with):
    client, _ = client_with(NIGHT)
    params = {"from": "2026-11-14", "to": "2026-11-14", "limit": 1}
    first = client.get("/events", params=params)
    second = client.get("/events", params={**params, "cursor": first.json()["next_cursor"]})
    assert ids(first) + ids(second) == ["sat-22h", "sat-23h59"]
    assert second.json()["next_cursor"] is None


def test_without_dates_there_is_no_date_filter(client_with):
    client, fake = client_with(NIGHT)
    client.get("/events")
    assert (fake.calls[-1]["filters"].starts_from, fake.calls[-1]["filters"].starts_before) == (None, None)


def test_to_before_from_is_rejected(client_with):
    client, fake = client_with(NIGHT)
    response = client.get("/events", params={"from": "2026-11-15", "to": "2026-11-14"})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "`to` (2026-11-14) is before `from` (2026-11-15)."
    assert fake.calls == []


@pytest.mark.parametrize("params", [{"from": "2026-13-01"}, {"to": "14/11/2026"}, {"from": "mañana"}])
def test_a_date_that_is_not_yyyy_mm_dd_is_rejected(client_with, params):
    client, fake = client_with(NIGHT)
    response = client.get("/events", params=params)
    assert response.status_code == 422
    assert response.json()["errors"][0]["loc"] == ["query", next(iter(params))]
    assert fake.calls == []


def test_start_times_come_in_buenos_aires_time_so_the_day_and_hour_read_as_is(client_with):
    client, _ = client_with([SATURDAY_NIGHT])
    item = client.get("/events").json()["items"][0]
    assert item["starts_at"] == "2026-11-14T22:00:00-03:00"  # stored as 2026-11-15 01:00 UTC
    assert datetime.fromisoformat(item["starts_at"]) == SATURDAY_NIGHT.starts_at  # same instant


def placed(id_: str, venue: str, hours: int = 0, **extra) -> Event:
    return event(id_, hours).model_copy(update={"venue": venue, **extra})


def test_venue_and_category_are_passed_to_the_filters(client_with):
    client, fake = client_with([event("e0", 0)])
    assert client.get("/events", params={"venue": " Niceto Club ", "category": "concert"}).status_code == 200
    assert fake.calls[-1]["filters"] == EventFilters(venue="Niceto Club", category="concert")


@pytest.mark.parametrize("params", [{}, {"venue": ""}, {"venue": "   "}])
def test_without_a_venue_or_category_there_is_no_such_filter(client_with, params):
    client, fake = client_with([event("e0", 0)])
    client.get("/events", params=params)
    assert (fake.calls[-1]["filters"].venue, fake.calls[-1]["filters"].category) == (None, None)


def test_the_venue_combines_with_the_search_the_dates_and_the_cursor(client_with):
    stored = [
        placed("sat-niceto-a", "Niceto Club").model_copy(update={"starts_at": SATURDAY_NIGHT.starts_at}),
        placed("sat-niceto-b", "Niceto Club").model_copy(update={"starts_at": SATURDAY_LAST_MINUTE.starts_at}),
        placed("sat-colon", "Teatro Colón").model_copy(update={"starts_at": SATURDAY_NIGHT.starts_at}),
        placed("sun-niceto", "Niceto Club").model_copy(update={"starts_at": SUNDAY_MIDNIGHT.starts_at}),
    ]
    client, fake = client_with(stored)
    params = {"venue": "Niceto Club", "q": "show", "from": "2026-11-14", "to": "2026-11-14", "limit": 1}
    first = client.get("/events", params=params)
    second = client.get("/events", params={**params, "cursor": first.json()["next_cursor"]})
    assert ids(first) + ids(second) == ["sat-niceto-a", "sat-niceto-b"]
    assert second.json()["next_cursor"] is None
    filters = fake.calls[-1]["filters"]
    assert (filters.q, filters.venue, filters.category) == ("show", "Niceto Club", None)
    assert (filters.starts_from, filters.starts_before) == (
        datetime(2026, 11, 14, 3, 0, tzinfo=UTC), datetime(2026, 11, 15, 3, 0, tzinfo=UTC),
    )


def test_the_category_filters_the_page(client_with):
    client, _ = client_with([event("e0", 0), placed("e1", "Teatro Colón", 1, category="theatre")])
    assert ids(client.get("/events", params={"category": "theatre"})) == ["e1"]


def test_an_unknown_category_is_rejected(client_with):
    client, fake = client_with([event("e0", 0)])
    response = client.get("/events", params={"category": "opera"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["loc"] == ["query", "category"]
    assert fake.calls == []


def test_a_venue_longer_than_100_characters_is_rejected(client_with):
    client, fake = client_with([event("e0", 0)])
    response = client.get("/events", params={"venue": "a" * 101})
    assert response.status_code == 422
    assert response.json()["errors"][0]["loc"] == ["query", "venue"]
    assert fake.calls == []
    assert client.get("/events", params={"venue": "a" * 100}).status_code == 200


def test_every_event_says_when_it_was_first_seen(client_with):
    client, _ = client_with([event("e0", 1, seen_days_ago=2)])
    (item,) = client.get("/events").json()["items"]
    assert datetime.fromisoformat(item["first_seen_at"]) == NOW - timedelta(days=2)


def test_by_default_events_are_listed_by_date(client_with):
    client, fake = client_with([event("late", 5, seen_days_ago=0), event("soon", 1, seen_days_ago=9)])
    assert ids(client.get("/events")) == ["soon", "late"]
    assert fake.calls[-1]["sort"] == "starts_at"


def test_sort_announced_lists_the_newest_announcement_first(client_with):
    client, fake = client_with([event("old", 1, seen_days_ago=9), event("new", 5, seen_days_ago=1), event("mid", 3, seen_days_ago=4)])
    assert ids(client.get("/events", params={"sort": "announced"})) == ["new", "mid", "old"]
    assert fake.calls[-1]["sort"] == "announced"


def test_sort_announced_pages_with_the_cursor_without_repeating_or_skipping(client_with):
    client, _ = client_with([event(f"e{i}", i, seen_days_ago=i % 2) for i in range(5)])
    seen, cursor = [], None
    while True:
        params = {"sort": "announced", "limit": 2, **({"cursor": cursor} if cursor else {})}
        response = client.get("/events", params=params)
        seen += ids(response)
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    assert seen == ["e4", "e2", "e0", "e3", "e1"]


@pytest.mark.parametrize("first_sort,second_sort", [("starts_at", "announced"), ("announced", "starts_at")])
def test_a_cursor_only_works_with_the_sort_that_issued_it(client_with, first_sort, second_sort):
    client, _ = client_with([event(f"e{i}", i) for i in range(3)])
    cursor = client.get("/events", params={"sort": first_sort, "limit": 1}).json()["next_cursor"]
    response = client.get("/events", params={"sort": second_sort, "cursor": cursor})
    assert response.status_code == 400
    assert response.json()["title"] == "Invalid cursor"


def test_an_unknown_sort_is_rejected(client_with):
    client, _ = client_with([])
    assert client.get("/events", params={"sort": "title"}).status_code == 422


def test_announced_from_is_the_start_of_that_buenos_aires_day(client_with):
    client, fake = client_with([])
    client.get("/events", params={"announced_from": "2026-11-09"})
    assert fake.calls[-1]["filters"].announced_from == datetime(2026, 11, 9, 3, 0, tzinfo=timezone.utc)


def test_without_announced_from_there_is_no_such_filter(client_with):
    client, fake = client_with([])
    client.get("/events")
    assert fake.calls[-1]["filters"].announced_from is None


def test_announced_from_combines_with_the_announced_sort(client_with):
    client, _ = client_with([event("fresh", 1, seen_days_ago=0), event("stale", 2, seen_days_ago=30)])
    response = client.get("/events", params={"sort": "announced", "announced_from": "2026-10-26"})
    assert ids(response) == ["fresh"]


def test_announced_from_that_is_not_a_date_is_rejected(client_with):
    client, _ = client_with([])
    assert client.get("/events", params={"announced_from": "hace 14 dias"}).status_code == 422
