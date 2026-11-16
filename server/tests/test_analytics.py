import logging
import uuid
from datetime import datetime, timezone

import httpx
import pytest

from app.analytics import DEFAULT_HOST, environment_name, forward_ticket_click, ticket_click_payload
from app.domain.ticket_redirect import TicketClick

AT = datetime(2026, 11, 15, 21, 14, 37, tzinfo=timezone.utc)
CLICK = TicketClick("venti-ultraligera-en-niceto-club", "venti-ultraligera-en-niceto-club-20261115T2000", "Venti", "show", AT, "Ultraligera en Niceto Club", "Niceto Club", "ios")


class FakePost:
    def __init__(self, status: int = 200, error: Exception | None = None):
        self.calls, self.status, self.error = [], status, error

    def __call__(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        if self.error:
            raise self.error
        return httpx.Response(self.status, request=httpx.Request("POST", url))


@pytest.fixture(autouse=True)
def no_posthog_env(monkeypatch):
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_HOST", raising=False)


def test_a_click_is_an_anonymous_event_with_only_what_the_count_has():
    payload = ticket_click_payload("phc_key", CLICK, "prod")
    assert payload["api_key"] == "phc_key"
    assert payload["event"] == "ticket link clicked"
    assert payload["timestamp"] == "2026-11-15T21:14:37+00:00"
    assert payload["properties"] == {
        "show_key": "venti-ultraligera-en-niceto-club",
        "show_name": "Ultraligera en Niceto Club",
        "venue": "Niceto Club",
        "device": "ios",
        "environment": "prod",
        "event_id": "venti-ultraligera-en-niceto-club-20261115T2000",
        "vendor": "Venti",
        "source": "show",
        "$process_person_profile": False,  # no person profile: nobody is identified
        "$geoip_disable": True,  # the request comes from our server, so its location means nothing
    }
    assert set(payload) == {"api_key", "event", "distinct_id", "properties", "timestamp"}


def test_every_event_gets_its_own_random_id_so_nothing_links_two_clicks_to_one_person():
    first, second = ticket_click_payload("k", CLICK, "dev")["distinct_id"], ticket_click_payload("k", CLICK, "dev")["distinct_id"]
    assert first != second
    assert uuid.UUID(first) and uuid.UUID(second)


def test_without_a_key_nothing_is_sent(monkeypatch):
    post = FakePost()
    forward_ticket_click(CLICK, post=post)
    monkeypatch.setenv("POSTHOG_API_KEY", "   ")
    forward_ticket_click(CLICK, post=post)
    assert post.calls == []


def test_with_a_key_the_event_goes_to_the_us_cloud_by_default_with_a_short_timeout(monkeypatch):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    post = FakePost()
    forward_ticket_click(CLICK, post=post)
    [call] = post.calls
    assert call["url"] == f"{DEFAULT_HOST}/i/v0/e/" == "https://us.i.posthog.com/i/v0/e/"
    assert call["json"]["api_key"] == "phc_key" and call["json"]["event"] == "ticket link clicked"
    assert 0 < call["timeout"] <= 5


@pytest.mark.parametrize("host", ["https://eu.i.posthog.com", "https://eu.i.posthog.com/", " https://eu.i.posthog.com "])
def test_the_host_can_be_the_eu_cloud_or_a_self_hosted_one(monkeypatch, host):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    monkeypatch.setenv("POSTHOG_HOST", host)
    post = FakePost()
    forward_ticket_click(CLICK, post=post)
    assert post.calls[0]["url"] == "https://eu.i.posthog.com/i/v0/e/"


@pytest.mark.parametrize(
    "error",
    [httpx.ConnectError("no route"), httpx.ReadTimeout("slow"), httpx.UnsupportedProtocol("bad host"), httpx.InvalidURL("bad")],
)
def test_a_network_problem_never_gets_out_of_the_forwarder(monkeypatch, caplog, error):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    with caplog.at_level(logging.WARNING):
        forward_ticket_click(CLICK, post=FakePost(error=error))
    assert "PostHog" in caplog.text


def test_an_error_answer_is_logged_and_never_raised(monkeypatch, caplog):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    with caplog.at_level(logging.WARNING):
        forward_ticket_click(CLICK, post=FakePost(status=503))
    assert "PostHog" in caplog.text and "503" in caplog.text


def test_the_log_never_carries_the_key(monkeypatch, caplog):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_secret_key")
    with caplog.at_level(logging.DEBUG):
        forward_ticket_click(CLICK, post=FakePost(error=httpx.ConnectError("no route")))
        forward_ticket_click(CLICK, post=FakePost(status=500))
    assert "phc_secret_key" not in caplog.text


@pytest.mark.parametrize(
    "value, expected",
    [(None, "dev"), ("", "dev"), ("dev", "dev"), ("test", "test"), (" PROD ", "prod"), ("production", "unknown"), ("staging", "unknown")],
)
def test_the_environment_is_dev_test_or_prod_and_anything_else_is_called_unknown(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", value)
    assert environment_name() == expected


def test_a_sent_click_carries_the_environment_the_server_runs_in(monkeypatch):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_key")
    monkeypatch.setenv("APP_ENV", "test")
    post = FakePost()
    forward_ticket_click(CLICK, post=post)
    assert post.calls[0]["json"]["properties"]["environment"] == "test"
    assert post.calls[0]["json"]["properties"]["show_name"] == "Ultraligera en Niceto Club"


def test_a_click_without_a_known_name_sends_no_name():
    click = TicketClick("s", "s-20261115T2000", None, "other", AT)
    assert ticket_click_payload("k", click, "dev")["properties"]["show_name"] is None
