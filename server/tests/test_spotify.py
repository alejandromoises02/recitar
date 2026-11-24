import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app.domain.event import Event, TicketLink
from app.events_repository import get_spotify_artist_id, upsert_events
from app.spotify import (
    SEARCH_URL, TOKEN_URL, MissingSpotifyCredentialsError, look_up_artists, pick_artist, spotify_credentials,
)

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
VALEN_VARGAS = "67oZkRi3cta1wNxN3KoFt5"


def results(name: str) -> list[dict]:
    return json.loads((FIXTURES / f"spotify_{name}.json").read_text(encoding="utf-8"))["artists"]["items"]


def test_the_artist_whose_name_matches_is_picked_even_when_it_is_not_first():
    # Spotify lists "Valen" and another act before "Valen Vargas" (seen on 2026-11-24).
    assert pick_artist(results("valen_vargas"), "Valen Vargas") == VALEN_VARGAS


def test_names_match_without_minding_case_accents_or_spaces():
    assert pick_artist(results("valen_vargas"), "VALEN  VARGAS") == VALEN_VARGAS
    assert pick_artist(results("valen_vargas"), "Válen Vargas") == VALEN_VARGAS


def test_a_search_with_no_artist_of_that_name_picks_nothing():
    # Spotify returns ten loosely related artists even for a made-up name.
    assert len(results("not_found")) == 10
    assert pick_artist(results("not_found"), "zzqx nonexistent band qq") is None
    assert pick_artist([], "Valen Vargas") is None


def test_the_credentials_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "the-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "the-secret")
    assert spotify_credentials() == ("the-id", "the-secret")


def test_missing_credentials_say_what_to_set(monkeypatch):
    monkeypatch.setattr("app.spotify.load_dotenv", lambda *_a, **_k: None)
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "the-id")
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    with pytest.raises(MissingSpotifyCredentialsError, match="SPOTIFY_CLIENT_SECRET"):
        spotify_credentials()


class FakeSpotify:
    def __init__(self, answers: dict[str, httpx.Response]):
        self.answers = answers
        self.searches: list[dict[str, str]] = []
        self.token_requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == TOKEN_URL:
            self.token_requests.append(request)
            return httpx.Response(200, json={"access_token": "tok", "token_type": "Bearer", "expires_in": 3600})
        assert str(request.url).startswith(SEARCH_URL)
        assert request.headers["Authorization"] == "Bearer tok"
        params = dict(request.url.params)
        self.searches.append(params)
        return self.answers.get(params["q"], httpx.Response(200, json={"artists": {"items": []}}))


def _event(id_: str, artist: str | None, days: int = 5) -> Event:
    return Event(
        id=id_, category="concert", title=artist or "Fiesta", artist=artist, venue="Niceto Club", city="Buenos Aires",
        region="AR-C", country="AR", starts_at=NOW + timedelta(days=days),
        ticket_links=[TicketLink(vendor="X", url="https://x")], source_url="https://x", updated_at=NOW,
    )


def _artist_row(conn, name: str):
    return conn.execute(text("SELECT spotify_id, checked_at FROM artists WHERE name = :name"), {"name": name}).one_or_none()


def test_upcoming_artists_are_looked_up_once_and_a_failure_does_not_stop_the_rest(db_engine):
    fake = FakeSpotify({
        "Valen Vargas": httpx.Response(200, json=json.loads((FIXTURES / "spotify_valen_vargas.json").read_text())),
        "Mugre": httpx.Response(500),
    })
    sleeps: list[float] = []
    with db_engine.begin() as conn:
        upsert_events(conn, [
            _event("a-1-20261129T2100", "Valen Vargas"),
            _event("a-1-20261130T2100", "Valen Vargas"),  # two dates, one search
            _event("a-2-20261129T2100", "Mugre"),
            _event("a-3-20261129T2100", "Banda Inventada"),
            _event("a-4-20261129T2100", None),  # no artist read from the title
            _event("a-5-20261120T2100", "Ya Tocó", days=-4),  # already played
        ])
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            report = look_up_artists(conn, client, ("the-id", "the-secret"), NOW, delay=0.2, sleep=sleeps.append)
        assert _artist_row(conn, "Valen Vargas") == (VALEN_VARGAS, NOW)
        assert _artist_row(conn, "Banda Inventada") == (None, NOW)  # checked: not asked again tomorrow
        assert _artist_row(conn, "Mugre") is None  # failed: asked again next time
        assert _artist_row(conn, "Ya Tocó") is None
        assert get_spotify_artist_id(conn, "Valen Vargas") == VALEN_VARGAS
        assert get_spotify_artist_id(conn, "Banda Inventada") is None
    assert [q["q"] for q in fake.searches] == ["Banda Inventada", "Mugre", "Valen Vargas"]
    assert {(q["type"], q["limit"]) for q in fake.searches} == {("artist", "10")}
    [token] = fake.token_requests
    assert token.headers["Authorization"] == "Basic " + base64.b64encode(b"the-id:the-secret").decode()
    assert token.content == b"grant_type=client_credentials"
    assert sleeps == [0.2, 0.2, 0.2]
    assert (report.found, report.missed, list(report.failed)) == (["Valen Vargas"], ["Banda Inventada"], ["Mugre"])


def test_an_artist_spotify_did_not_have_is_asked_again_after_a_month(db_engine):
    fake = FakeSpotify({})
    with db_engine.begin() as conn:
        upsert_events(conn, [_event("a-1-20261129T2100", "Banda Nueva"), _event("a-2-20261129T2100", "Banda Vieja")])
        conn.execute(text(
            "INSERT INTO artists (name, spotify_id, checked_at) VALUES "
            "('Banda Nueva', NULL, :recent), ('Banda Vieja', NULL, :old)"
        ), {"recent": NOW - timedelta(days=29), "old": NOW - timedelta(days=31)})
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            look_up_artists(conn, client, ("the-id", "the-secret"), NOW, delay=0, sleep=lambda _s: None)
        assert _artist_row(conn, "Banda Vieja") == (None, NOW)
    assert [q["q"] for q in fake.searches] == ["Banda Vieja"]


def test_an_artist_already_found_is_not_asked_again(db_engine):
    fake = FakeSpotify({})
    with db_engine.begin() as conn:
        upsert_events(conn, [_event("a-1-20261129T2100", "Valen Vargas")])
        conn.execute(text("INSERT INTO artists (name, spotify_id, checked_at) VALUES ('Valen Vargas', 'x', :old)"),
                     {"old": NOW - timedelta(days=90)})
        with httpx.Client(transport=httpx.MockTransport(fake)) as client:
            report = look_up_artists(conn, client, ("the-id", "the-secret"), NOW, delay=0, sleep=lambda _s: None)
    assert fake.searches == [] and fake.token_requests == []
    assert (report.found, report.missed, dict(report.failed)) == ([], [], {})


def test_a_rejected_token_stops_the_run_before_any_search(db_engine):
    def refuse(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == TOKEN_URL
        return httpx.Response(400, json={"error": "invalid_client"})

    with db_engine.begin() as conn:
        upsert_events(conn, [_event("a-1-20261129T2100", "Valen Vargas")])
        with httpx.Client(transport=httpx.MockTransport(refuse)) as client, pytest.raises(httpx.HTTPStatusError):
            look_up_artists(conn, client, ("bad", "bad"), NOW, delay=0, sleep=lambda _s: None)
