from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.featured import FEATURED_LIMIT, MAX_FEATURED, featured_store
from app.domain.event import Show, ShowDateTickets, TicketLink
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
TOKEN = "s3cret-" + "x" * 40


def show(id_: str) -> Show:
    return Show(
        id=id_, category="concert", title=f"Show {id_}", name=f"Show {id_}", venue="Niceto Club", source_url="https://venti.live/x",
        image_url=f"/media/{id_}.webp", image_origin="licensed", first_seen_at=NOW, updated_at=NOW,
        dates=[ShowDateTickets(id=f"{id_}-20261120T2100", starts_at=NOW + timedelta(days=11),
                               ticket_links=[TicketLink(vendor="Venti", url="https://venti.live/x")])],
    )


class FakeStore:
    def __init__(self, known=(), picked=(), announced=()):
        self.known, self.picked_items, self.announced_items = set(known), list(picked), list(announced)
        self.replaced: list[list[str]] = []

    def known_show_ids(self, ids):
        return self.known & set(ids)

    def replace(self, ids):
        self.replaced.append(list(ids))

    def picked(self, limit):
        return self.picked_items[:limit]

    def just_announced(self, limit):
        return self.announced_items[:limit]


@pytest.fixture
def client_with(monkeypatch):
    def make(store: FakeStore, token: str | None = TOKEN) -> TestClient:
        if token is None:
            monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        else:
            monkeypatch.setenv("ADMIN_TOKEN", token)
        app.dependency_overrides[featured_store] = lambda: store
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


def put(client, ids, auth: str | None = f"Bearer {TOKEN}"):
    headers = {"Authorization": auth} if auth is not None else {}
    return client.put("/featured", json={"show_ids": ids}, headers=headers)


# --- who may write ---------------------------------------------------------------------------------

def test_the_right_token_replaces_the_featured_list_in_order(client_with):
    store = FakeStore(known={"venti-a", "venti-b"})
    response = put(client_with(store), ["venti-b", "venti-a"])
    assert response.status_code == 200
    assert response.json() == {"show_ids": ["venti-b", "venti-a"]}
    assert store.replaced == [["venti-b", "venti-a"]]


@pytest.mark.parametrize("auth", [None, "", "Bearer", "Bearer ", f"Bearer {TOKEN}x", f"Bearer {TOKEN[:-1]}",
                                  f"Basic {TOKEN}", TOKEN, f"bearer{TOKEN}"])
def test_a_missing_or_wrong_token_is_401_and_changes_nothing(client_with, auth):
    store = FakeStore(known={"venti-a"})
    response = put(client_with(store), ["venti-a"], auth=auth)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert store.replaced == []


def test_the_scheme_is_case_insensitive(client_with):
    store = FakeStore(known={"venti-a"})
    assert put(client_with(store), ["venti-a"], auth=f"bearer {TOKEN}").status_code == 200


@pytest.mark.parametrize("token", [None, "", "   ", "short-token"])
def test_without_a_strong_admin_token_configured_writing_is_off(client_with, token):
    store = FakeStore(known={"venti-a"})
    response = put(client_with(store, token=token), ["venti-a"], auth=f"Bearer {token or ''}")
    assert response.status_code == 503
    assert store.replaced == []


def test_the_configured_token_is_read_without_surrounding_spaces(client_with):
    store = FakeStore(known={"venti-a"})
    assert put(client_with(store, token=f"  {TOKEN}\n"), ["venti-a"]).status_code == 200


def test_the_token_is_checked_before_the_body_shape(client_with):
    # (Malformed JSON is rejected by FastAPI before any dependency runs; it reveals nothing.)
    store = FakeStore()
    response = client_with(store).put("/featured", json={"show_ids": "not a list"})
    assert response.status_code == 401


# --- what may be written ---------------------------------------------------------------------------

def test_unknown_show_ids_are_rejected_by_name_and_nothing_is_stored(client_with):
    store = FakeStore(known={"venti-a"})
    response = put(client_with(store), ["venti-a", "venti-typo", "colon-nope"])
    assert response.status_code == 422
    assert response.json()["detail"] == "Unknown show ids: colon-nope, venti-typo."
    assert store.replaced == []


def test_repeated_ids_are_rejected(client_with):
    store = FakeStore(known={"venti-a"})
    assert put(client_with(store), ["venti-a", "venti-a"]).status_code == 422
    assert store.replaced == []


def test_more_than_the_maximum_is_rejected(client_with):
    ids = [f"venti-{i}" for i in range(MAX_FEATURED + 1)]
    store = FakeStore(known=ids)
    assert put(client_with(store), ids).status_code == 422
    assert store.replaced == []


def test_an_empty_list_clears_the_featured_shows(client_with):
    store = FakeStore()
    response = put(client_with(store), [])
    assert (response.status_code, store.replaced) == (200, [[]])


def test_ids_are_trimmed_before_checking(client_with):
    store = FakeStore(known={"venti-a"})
    assert put(client_with(store), [" venti-a "]).json() == {"show_ids": ["venti-a"]}


# --- reading -----------------------------------------------------------------------------------------

def test_reading_needs_no_token_and_gives_the_picked_shows(client_with):
    store = FakeStore(picked=[show("venti-b"), show("venti-a")], announced=[show("venti-z")])
    response = client_with(store, token=None).get("/featured")
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "picked"
    assert [s["id"] for s in body["items"]] == ["venti-b", "venti-a"]


def test_with_nothing_picked_it_falls_back_to_just_announced(client_with):
    store = FakeStore(announced=[show("venti-z"), show("venti-y")])
    body = client_with(store).get("/featured").json()
    assert body["kind"] == "just_announced"
    assert [s["id"] for s in body["items"]] == ["venti-z", "venti-y"]


def test_with_nothing_at_all_it_is_an_empty_list(client_with):
    assert client_with(FakeStore()).get("/featured").json() == {"kind": "just_announced", "items": []}


def test_reading_returns_at_most_the_limit(client_with):
    store = FakeStore(picked=[show(f"venti-{i}") for i in range(FEATURED_LIMIT + 3)])
    assert len(client_with(store).get("/featured").json()["items"]) == FEATURED_LIMIT


def test_the_write_endpoint_documents_its_bearer_token():
    schema = app.openapi()
    operation = schema["paths"]["/featured"]["put"]
    assert {"401", "422", "503"} <= set(operation["responses"])
    assert operation["security"]
    assert "security" not in schema["paths"]["/featured"]["get"]


def test_a_blank_id_is_rejected_as_invalid_not_as_unknown(client_with):
    store = FakeStore(known={"venti-a"})
    response = put(client_with(store), ["venti-a", "   "])
    assert response.status_code == 422
    assert response.json()["detail"] == "Some parameters are not valid."
    assert store.replaced == []


def test_unknown_fields_in_the_body_are_rejected(client_with):
    store = FakeStore(known={"venti-a"})
    response = client_with(store).put(
        "/featured", json={"show_ids": ["venti-a"], "showIds": []}, headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 422
    assert store.replaced == []
