from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.go import click_forwarder, click_recorder, go_event_source
from app.domain.event import Event, TicketLink
from app.main import app

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def event(id_: str = "movistar-becerra-20261120T2100", links=(("Venti", "https://venti.live/x"), ("Livepass", "https://livepass.com.ar/x"))) -> Event:
    return Event(
        id=id_, category="concert", title="María Becerra", venue="Movistar Arena", starts_at=NOW,
        ticket_links=[TicketLink(vendor=vendor, url=url) for vendor, url in links],
        source_url="https://www.movistararena.com.ar/show/x", updated_at=NOW,
    )


class Recorder:
    def __init__(self, fail: bool = False):
        self.clicks, self.fail = [], fail

    def __call__(self, click):
        if self.fail:
            raise RuntimeError("database is down")
        self.clicks.append(click)


@pytest.fixture
def go():
    def make(stored: list[Event], recorder: Recorder | None = None, forwarder: Recorder | None = None):
        by_id = {e.id: e for e in stored}
        recorder = recorder or Recorder()
        forwarder = forwarder if forwarder is not None else Recorder()
        app.dependency_overrides[go_event_source] = lambda: by_id.get
        app.dependency_overrides[click_recorder] = lambda: recorder
        app.dependency_overrides[click_forwarder] = lambda: forwarder
        client = TestClient(app, follow_redirects=False, headers={"user-agent": BROWSER})
        client.forwarder = forwarder
        return client, recorder

    yield make
    app.dependency_overrides.clear()


def test_the_visitor_is_sent_to_the_first_ticket_link_with_our_utm_source(go):
    client, _ = go([event()])
    response = client.get("/go/movistar-becerra-20261120T2100")
    assert response.status_code == 302
    assert response.headers["location"] == "https://venti.live/x?utm_source=recitar"


def test_the_redirect_is_never_cached(go):
    client, _ = go([event()])
    assert client.get("/go/movistar-becerra-20261120T2100").headers["cache-control"] == "no-store"


def test_the_asked_vendor_is_used_when_the_date_sells_through_several(go):
    client, _ = go([event()])
    response = client.get("/go/movistar-becerra-20261120T2100", params={"v": "Livepass"})
    assert response.headers["location"] == "https://livepass.com.ar/x?utm_source=recitar"


def test_a_date_without_ticket_links_goes_to_the_source_page(go):
    client, recorder = go([event(links=())])
    response = client.get("/go/movistar-becerra-20261120T2100")
    assert response.headers["location"] == "https://www.movistararena.com.ar/show/x?utm_source=recitar"
    assert recorder.clicks[0].vendor is None


def test_the_click_is_stored_with_the_show_the_date_the_vendor_and_where_it_came_from(go):
    client, recorder = go([event()])
    client.get("/go/movistar-becerra-20261120T2100", params={"v": "Livepass", "from": "spotlight"})
    [click] = recorder.clicks
    assert (click.show_key, click.event_id, click.vendor, click.source) == (
        "movistar-becerra", "movistar-becerra-20261120T2100", "Livepass", "spotlight",
    )
    assert abs((click.at - datetime.now(timezone.utc)).total_seconds()) < 60


def test_the_vendor_stored_is_the_one_that_was_used_not_the_one_asked(go):
    client, recorder = go([event()])
    client.get("/go/movistar-becerra-20261120T2100", params={"v": "Nobody"})
    assert recorder.clicks[0].vendor == "Venti"


@pytest.mark.parametrize("asked, stored", [(None, "show"), ("show", "show"), ("spotlight", "spotlight"), ("anything-else", "other"), ("x" * 500, "other")])
def test_where_it_came_from_is_one_of_the_known_places_or_other(go, asked, stored):
    client, recorder = go([event()])
    response = client.get("/go/movistar-becerra-20261120T2100", params={} if asked is None else {"from": asked})
    assert response.status_code == 302
    assert recorder.clicks[0].source == stored


def test_a_date_that_does_not_exist_is_not_found_and_not_counted(go):
    client, recorder = go([event()])
    response = client.get("/go/movistar-nope-20261120T2100")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert recorder.clicks == []


def test_the_destination_never_comes_from_the_request(go):
    client, _ = go([event()])
    response = client.get("/go/movistar-becerra-20261120T2100", params={"url": "https://evil.example", "to": "https://evil.example", "next": "//evil.example"})
    assert response.headers["location"] == "https://venti.live/x?utm_source=recitar"


def test_a_date_whose_only_links_are_not_web_links_is_not_found(go):
    unsafe = event(links=(("Venti", "javascript:alert(1)"),)).model_copy(update={"source_url": "javascript:alert(1)"})
    client, recorder = go([unsafe])
    assert client.get("/go/movistar-becerra-20261120T2100").status_code == 404
    assert recorder.clicks == []


def test_a_crawler_is_redirected_but_not_counted(go):
    client, recorder = go([event()])
    response = client.get("/go/movistar-becerra-20261120T2100", headers={"user-agent": "Slackbot-LinkExpanding 1.0"})
    assert response.status_code == 302
    assert recorder.clicks == []


def test_the_visitor_is_still_redirected_when_the_click_cannot_be_stored(go):
    client, _ = go([event()], Recorder(fail=True))
    response = client.get("/go/movistar-becerra-20261120T2100")
    assert response.status_code == 302
    assert response.headers["location"] == "https://venti.live/x?utm_source=recitar"


def test_the_route_is_in_the_api_schema_as_a_redirect_with_a_not_found():
    operation = app.openapi()["paths"]["/go/{event_id}"]["get"]
    assert {"302", "404"} <= set(operation["responses"])


def test_the_counted_click_is_also_handed_to_the_analytics_forwarder(go):
    client, recorder = go([event()])
    client.get("/go/movistar-becerra-20261120T2100", params={"v": "Livepass", "from": "spotlight"})
    assert client.forwarder.clicks == recorder.clicks and len(recorder.clicks) == 1


def test_a_crawler_or_an_unknown_date_is_not_forwarded(go):
    client, _ = go([event()])
    client.get("/go/movistar-becerra-20261120T2100", headers={"user-agent": "Slackbot-LinkExpanding 1.0"})
    client.get("/go/movistar-nope-20261120T2100")
    assert client.forwarder.clicks == []


def test_the_click_is_forwarded_even_when_it_could_not_be_stored_and_the_visitor_still_gets_through(go):
    client, _ = go([event()], Recorder(fail=True))
    response = client.get("/go/movistar-becerra-20261120T2100")
    assert response.status_code == 302
    assert len(client.forwarder.clicks) == 1


def test_a_forwarder_that_fails_does_not_change_the_redirect(go):
    client, _ = go([event()], forwarder=Recorder(fail=True))
    response = client.get("/go/movistar-becerra-20261120T2100")
    assert response.status_code == 302
    assert response.headers["location"] == "https://venti.live/x?utm_source=recitar"



def test_the_forwarded_click_carries_the_readable_show_name(go):
    client, _ = go([event()])
    client.get("/go/movistar-becerra-20261120T2100")
    assert client.forwarder.clicks[0].show_name == event().name


def test_the_forwarded_click_carries_the_venue_and_the_device_class_of_the_visitor(go):
    client, _ = go([event()])
    client.get("/go/movistar-becerra-20261120T2100", headers={"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"})
    click = client.forwarder.clicks[0]
    assert (click.venue, click.device) == ("Movistar Arena", "ios")
