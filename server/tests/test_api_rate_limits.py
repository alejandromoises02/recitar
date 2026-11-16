"""The public endpoints that count things (/go, /track) are limited per caller, and /track bodies are capped."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.go import click_forwarder, click_recorder, go_event_source
from app.api.rate_limit import RateLimiter
from app.api.track import track_forwarder
from app.domain.event import Event, TicketLink
from app.main import MAX_TRACK_BODY_BYTES, create_app

BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SESSION = "3f2b8c1e-9d4a-4e7b-8a61-0c5d2f7e9b13"
NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
EVENT = Event(
    id="movistar-becerra-20261120T2100", category="concert", title="María Becerra", venue="Movistar Arena", starts_at=NOW,
    ticket_links=[TicketLink(vendor="Venti", url="https://venti.live/x")],
    source_url="https://www.movistararena.com.ar/show/x", updated_at=NOW,
)
VISIT = {"event": "visit started", "session_id": SESSION}


class Calls(list):
    def __call__(self, *args):
        self.append(args)


@pytest.fixture
def limited(tmp_path):
    """An app whose limits are small enough to reach, with the database and the analytics tool faked."""
    app = create_app(
        media_dir=tmp_path,
        rate_limits={"go": RateLimiter(limit=2, window_seconds=60), "track": RateLimiter(limit=2, window_seconds=60)},
    )
    recorded, forwarded, tracked = Calls(), Calls(), Calls()
    app.dependency_overrides[go_event_source] = lambda: {EVENT.id: EVENT}.get
    app.dependency_overrides[click_recorder] = lambda: recorded
    app.dependency_overrides[click_forwarder] = lambda: forwarded
    app.dependency_overrides[track_forwarder] = lambda: tracked

    def client(ip: str = "1.2.3.4") -> TestClient:
        return TestClient(app, headers={"user-agent": BROWSER}, client=(ip, 50000), follow_redirects=False)

    client.recorded, client.forwarded, client.tracked = recorded, forwarded, tracked
    return client


def test_track_refuses_a_caller_over_the_limit_with_429_and_when_to_retry(limited):
    caller = limited()
    assert [caller.post("/track", json=VISIT).status_code for _ in range(2)] == [204, 204]
    refused = caller.post("/track", json=VISIT)
    assert refused.status_code == 429
    assert refused.headers["content-type"] == "application/problem+json"
    assert refused.json()["title"] == "Too many requests"
    assert 1 <= int(refused.headers["retry-after"]) <= 60
    assert len(limited.tracked) == 2


def test_track_counts_each_caller_apart(limited):
    for _ in range(3):
        limited("1.2.3.4").post("/track", json=VISIT)
    assert limited("5.6.7.8").post("/track", json=VISIT).status_code == 204


def test_go_over_the_limit_still_sends_the_visitor_to_the_tickets_but_does_not_count_the_click(limited):
    caller = limited()
    answers = [caller.get(f"/go/{EVENT.id}") for _ in range(3)]
    assert [a.status_code for a in answers] == [302, 302, 302]
    assert all(a.headers["location"].startswith("https://venti.live/x") for a in answers)
    assert len(limited.recorded) == 2
    assert len(limited.forwarded) == 2


def test_go_and_track_have_separate_limits(limited):
    caller = limited()
    for _ in range(3):
        caller.post("/track", json=VISIT)
    caller.get(f"/go/{EVENT.id}")
    assert len(limited.recorded) == 1


def test_reading_endpoints_are_not_limited(limited):
    caller = limited()
    assert all(caller.get("/health").status_code == 200 for _ in range(5))


def test_a_track_body_over_the_cap_is_refused_with_413_before_it_is_read(limited):
    body = b'{"event": "visit started", "session_id": "' + SESSION.encode() + b'", "x": "' + b"a" * MAX_TRACK_BODY_BYTES + b'"}'
    refused = limited().post("/track", content=body, headers={"content-type": "application/json"})
    assert refused.status_code == 413
    assert refused.headers["content-type"] == "application/problem+json"
    assert refused.json()["title"] == "Request body too large"
    assert limited.tracked == []


def test_a_streamed_track_body_without_a_length_is_cut_at_the_cap(limited):
    def chunks():
        yield b'{"event": "visit started", "x": "'
        for _ in range(MAX_TRACK_BODY_BYTES // 512 + 1):
            yield b"a" * 512
        yield b'"}'

    refused = limited().post("/track", content=chunks(), headers={"content-type": "application/json"})
    assert refused.status_code == 413
    assert limited.tracked == []


def test_a_track_body_right_at_the_cap_is_still_read(limited):
    padding = MAX_TRACK_BODY_BYTES - len(f'{{"event": "visit started", "session_id": "{SESSION}"}}')
    body = b'{"event": "visit started", "session_id": "' + SESSION.encode() + b'"' + b" " * padding + b"}"
    assert len(body) == MAX_TRACK_BODY_BYTES
    assert limited().post("/track", content=body, headers={"content-type": "application/json"}).status_code == 204


def test_an_over_limit_or_too_large_answer_keeps_cors_headers_for_the_web_app(tmp_path):
    app = create_app(media_dir=tmp_path, origins=["https://recitar.example"], rate_limits={"track": RateLimiter(limit=1, window_seconds=60)})
    app.dependency_overrides[track_forwarder] = lambda: Calls()
    caller = TestClient(app, headers={"user-agent": BROWSER, "origin": "https://recitar.example"})
    caller.post("/track", json=VISIT)
    refused = caller.post("/track", json=VISIT)
    assert refused.status_code == 429
    assert refused.headers["access-control-allow-origin"] == "https://recitar.example"
    huge = caller.post("/track", content=b"a" * (MAX_TRACK_BODY_BYTES + 1), headers={"content-type": "application/json"})
    assert huge.status_code == 413
    assert huge.headers["access-control-allow-origin"] == "https://recitar.example"
