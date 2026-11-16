import httpx
import pytest
from fastapi.testclient import TestClient

from app.analytics import forward_track, track_payload
from app.api.track import track_forwarder
from app.domain.track_event import TrackEvent
from app.main import app, create_app

BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SESSION = "3f2b8c1e-9d4a-4e7b-8a61-0c5d2f7e9b13"


class Recorder:
    def __init__(self, fail: bool = False):
        self.events, self.devices, self.fail = [], [], fail

    def __call__(self, event, device):
        if self.fail:
            raise RuntimeError("analytics is down")
        self.events.append(event)
        self.devices.append(device)


@pytest.fixture
def track():
    forwarder = Recorder()
    app.dependency_overrides[track_forwarder] = lambda: forwarder
    client = TestClient(app, headers={"user-agent": BROWSER})
    client.forwarder = forwarder
    yield client
    app.dependency_overrides.clear()


def visit(**extra):
    return {"event": "visit started", "session_id": SESSION, **extra}


def test_a_visit_is_accepted_and_forwarded_without_any_answer_body(track):
    response = track.post("/track", json=visit())
    assert response.status_code == 204 and response.content == b""
    assert [e.event for e in track.forwarder.events] == ["visit started"]
    assert track.forwarder.events[0].session_id == SESSION


def test_opening_a_show_carries_which_show_by_key_and_name(track):
    body = {"event": "show opened", "session_id": SESSION, "show_key": "venti-ultraligera-en-niceto-club", "show_name": "Ultraligera en Niceto Club", "venue": "Niceto Club"}
    assert track.post("/track", json=body).status_code == 204
    event = track.forwarder.events[0]
    assert (event.show_key, event.show_name, event.venue) == ("venti-ultraligera-en-niceto-club", "Ultraligera en Niceto Club", "Niceto Club")


def test_a_show_opening_without_the_show_is_refused(track):
    assert track.post("/track", json={"event": "show opened", "session_id": SESSION}).status_code == 422
    assert track.forwarder.events == []


def test_using_a_filter_carries_which_filter_and_its_value(track):
    assert track.post("/track", json={"event": "filter used", "session_id": SESSION, "filter": "venue", "value": "Niceto Club"}).status_code == 204
    event = track.forwarder.events[0]
    assert (event.filter, event.value) == ("venue", "Niceto Club")


def test_a_filter_event_without_which_filter_is_refused(track):
    assert track.post("/track", json={"event": "filter used", "session_id": SESSION, "value": "x"}).status_code == 422


def test_what_was_typed_in_the_search_is_never_kept(track):
    track.post("/track", json={"event": "filter used", "session_id": SESSION, "filter": "search", "value": "mi nombre es Ana"})
    event = track.forwarder.events[0]
    assert event.filter == "search" and event.value is None


@pytest.mark.parametrize(
    "body",
    [
        {"event": "purchase", "session_id": SESSION},  # not an event we know
        {"event": "visit started", "session_id": "short"},
        {"event": "visit started", "session_id": "has spaces and is long enough"},
        {"event": "visit started", "session_id": "x" * 65},
        {"event": "visit started"},
        {"event": "show opened", "session_id": SESSION, "show_key": "Has Spaces/And Slash"},
        {"event": "show opened", "session_id": SESSION, "show_key": "a" * 201},
        {"event": "show opened", "session_id": SESSION, "show_key": "ok-key", "show_name": "n" * 121},
        {"event": "show opened", "session_id": SESSION, "show_key": "ok-key", "venue": "v" * 121},
        {"event": "filter used", "session_id": SESSION, "filter": "password", "value": "x"},
        {"event": "filter used", "session_id": SESSION, "filter": "venue", "value": "v" * 61},
        {"event": "visit started", "session_id": SESSION, "ip": "1.2.3.4"},  # nothing else is accepted
    ],
)
def test_anything_unexpected_is_refused_and_not_forwarded(track, body):
    assert track.post("/track", json=body).status_code == 422
    assert track.forwarder.events == []


def test_a_crawler_is_answered_but_not_forwarded(track):
    response = track.post("/track", json=visit(), headers={"user-agent": "Googlebot/2.1"})
    assert response.status_code == 204
    assert track.forwarder.events == []


def test_a_forwarder_that_fails_does_not_change_the_answer():
    app.dependency_overrides[track_forwarder] = lambda: Recorder(fail=True)
    try:
        client = TestClient(app, headers={"user-agent": BROWSER})
        assert client.post("/track", json=visit()).status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_the_route_is_in_the_api_schema_as_a_post_with_no_content():
    operation = app.openapi()["paths"]["/track"]["post"]
    assert "204" in operation["responses"] and "422" in operation["responses"]


# the event as PostHog gets it

def event(**extra) -> TrackEvent:
    return TrackEvent(**visit(**extra))


def test_a_visit_is_one_anonymous_event_keyed_by_the_session_id():
    payload = track_payload("phc_key", event(), "prod", "ios")
    assert payload["api_key"] == "phc_key" and payload["event"] == "visit started"
    assert payload["distinct_id"] == SESSION
    assert payload["properties"] == {
        "environment": "prod",
        "device": "ios",
        "$process_person_profile": False,
        "$geoip_disable": True,
    }
    assert set(payload) == {"api_key", "event", "distinct_id", "properties"}


def test_show_and_filter_details_are_properties_and_left_out_when_absent():
    shown = TrackEvent(event="show opened", session_id=SESSION, show_key="a-b", show_name="A B", venue="Niceto Club")
    assert track_payload("k", shown, "dev", "desktop")["properties"]["show_key"] == "a-b"
    assert track_payload("k", shown, "dev", "desktop")["properties"]["show_name"] == "A B"
    assert track_payload("k", shown, "dev", "desktop")["properties"]["venue"] == "Niceto Club"
    filtered = TrackEvent(event="filter used", session_id=SESSION, filter="when", value="weekend")
    properties = track_payload("k", filtered, "dev", "desktop")["properties"]
    assert (properties["filter"], properties["value"]) == ("when", "weekend")
    assert "show_key" not in properties


class FakePost:
    def __init__(self, status: int = 200, error: Exception | None = None):
        self.calls, self.status, self.error = [], status, error

    def __call__(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        if self.error:
            raise self.error
        return httpx.Response(self.status, request=httpx.Request("POST", url))


@pytest.fixture(autouse=True)
def posthog_env(monkeypatch):
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_HOST", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)


def test_nothing_is_sent_without_a_posthog_key():
    post = FakePost()
    forward_track(event(), "desktop", post=post)
    assert post.calls == []


def test_with_a_key_the_event_goes_to_the_capture_address_with_the_environment(monkeypatch):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    monkeypatch.setenv("APP_ENV", "test")
    post = FakePost()
    forward_track(event(), "desktop", post=post)
    assert post.calls[0]["url"] == "https://us.i.posthog.com/i/v0/e/"
    assert post.calls[0]["json"]["properties"]["environment"] == "test"
    assert post.calls[0]["timeout"] == 3.0


def test_a_network_failure_is_logged_without_the_key_and_never_raised(monkeypatch, caplog):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_secret")
    forward_track(event(), "desktop", post=FakePost(error=httpx.ConnectTimeout("phc_secret timed out")))
    assert "phc_secret" not in caplog.text and "ConnectTimeout" in caplog.text


# who may call it from a web page

def test_our_own_web_app_may_post_the_track_events_and_nobody_else():
    client = TestClient(create_app(origins=["http://localhost:8081"]))
    ours = client.options("/track", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert ours.status_code == 200 and ours.headers["access-control-allow-origin"] == "http://localhost:8081"
    other = client.options("/track", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert other.status_code == 400


def test_the_admin_write_and_its_bearer_token_are_still_closed_to_web_pages():
    client = TestClient(create_app(origins=["http://localhost:8081"]))
    put = client.options("/featured", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "PUT"})
    assert put.status_code == 400
    auth = client.options("/track", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization"})
    assert auth.status_code == 400


@pytest.mark.parametrize(
    "agent, device",
    [
        (BROWSER, "desktop"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1", "ios"),
        ("Expo/1.0.0 CFNetwork/1494.0.7 Darwin/23.4.0", "ios"),
        ("okhttp/4.12.0", "android"),
    ],
)
def test_the_device_goes_with_the_event_but_never_the_browser_text(track, agent, device):
    track.post("/track", json=visit(), headers={"user-agent": agent})
    assert track.forwarder.devices == [device]


# the four events that say what interests people

@pytest.mark.parametrize("name", ["show shared", "more at venue clicked"])
def test_the_show_events_carry_the_show_and_cannot_come_without_it(track, name):
    body = {"event": name, "session_id": SESSION, "show_key": "venti-ultraligera-en-niceto-club", "show_name": "Ultraligera", "venue": "Niceto Club"}
    assert track.post("/track", json=body).status_code == 204
    assert track.forwarder.events[0].event == name
    assert track.post("/track", json={"event": name, "session_id": SESSION}).status_code == 422


def test_an_empty_result_says_which_filters_were_on_and_the_venue_and_date_asked_for(track):
    body = {"event": "no results", "session_id": SESSION, "filters": ["venue", "when"], "venue": "Niceto Club", "when": "weekend"}
    assert track.post("/track", json=body).status_code == 204
    event = track.forwarder.events[0]
    assert (event.filters, event.venue, event.when) == (["venue", "when"], "Niceto Club", "weekend")


@pytest.mark.parametrize(
    "extra",
    [
        {},  # no filters at all: an empty listing without filters says nothing about what people look for
        {"filters": []},
        {"filters": ["password"]},
        {"filters": ["venue", "when", "day", "search", "group", "venue"]},  # more than there are filters
        {"filters": ["venue"], "when": "Has Spaces"},
        {"filters": ["venue"], "when": "w" * 21},
    ],
)
def test_an_empty_result_without_valid_filters_is_refused(track, extra):
    assert track.post("/track", json={"event": "no results", "session_id": SESSION, **extra}).status_code == 422
    assert track.forwarder.events == []


def test_the_empty_result_details_are_properties_of_the_event():
    event = TrackEvent(event="no results", session_id=SESSION, filters=["search", "venue"], venue="Niceto Club", when="2026-12-05")
    properties = track_payload("k", event, "dev", "ios")["properties"]
    assert properties["filters"] == ["search", "venue"]
    assert (properties["venue"], properties["when"]) == ("Niceto Club", "2026-12-05")
    assert "show_key" not in properties
