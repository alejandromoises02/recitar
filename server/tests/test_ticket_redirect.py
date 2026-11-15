from datetime import datetime, timezone

import pytest

from app.domain.event import Event, TicketLink
from app.domain.ticket_redirect import Destination, destination, looks_like_bot, with_utm_source

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def event(links: list[tuple[str, str]], source_url: str = "https://www.movistararena.com.ar/show/x") -> Event:
    return Event(
        id="movistar-x-20261120T2100", category="concert", title="X", venue="Movistar Arena", starts_at=NOW,
        ticket_links=[TicketLink(vendor=vendor, url=url) for vendor, url in links], source_url=source_url, updated_at=NOW,
    )


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://tickets.example/x", "https://tickets.example/x?utm_source=recitar"),
        ("https://tickets.example/x?a=1", "https://tickets.example/x?a=1&utm_source=recitar"),
        ("https://tickets.example/x?a=1#top", "https://tickets.example/x?a=1&utm_source=recitar#top"),
        ("https://tickets.example/x?utm_source=other&a=1", "https://tickets.example/x?utm_source=recitar&a=1"),
        ("https://tickets.example/x?q=a%20b", "https://tickets.example/x?q=a%20b&utm_source=recitar"),
    ],
)
def test_utm_source_is_added_or_replaced_and_the_rest_of_the_link_is_kept(url, expected):
    assert with_utm_source(url) == expected


def test_the_link_of_the_asked_vendor_is_the_destination():
    both = event([("Venti", "https://venti.live/x"), ("Livepass", "https://livepass.com.ar/x")])
    assert destination(both, "Livepass") == Destination("https://livepass.com.ar/x", "Livepass")


def test_without_a_vendor_or_with_an_unknown_one_the_first_link_is_the_destination():
    both = event([("Venti", "https://venti.live/x"), ("Livepass", "https://livepass.com.ar/x")])
    assert destination(both, None) == Destination("https://venti.live/x", "Venti")
    assert destination(both, "Nobody") == Destination("https://venti.live/x", "Venti")


def test_a_date_without_ticket_links_goes_to_the_show_page_of_the_source():
    assert destination(event([]), None) == Destination("https://www.movistararena.com.ar/show/x", None)


@pytest.mark.parametrize(
    "bad",
    [
        "javascript:alert(1)", "data:text/html,x", "//evil.example/x", "ftp://files.example/x", "", "https:evil.example",
        "http://a.com\\@evil.com/",  # a browser reads the host differently from a parser: a.com or evil.com
        "https://user@evil.example/x", "https://user:pw@evil.example/x",
    ],
)
def test_only_web_links_are_a_destination(bad):
    assert destination(event([("Venti", bad), ("Livepass", "https://livepass.com.ar/x")]), None) == Destination("https://livepass.com.ar/x", "Livepass")
    assert destination(event([("Venti", bad)], source_url="https://src.example/x"), None) == Destination("https://src.example/x", None)
    assert destination(event([("Venti", bad)], source_url=bad), None) is None


@pytest.mark.parametrize(
    "agent",
    [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    ],
)
def test_a_browser_is_not_a_bot(agent):
    assert looks_like_bot(agent) is False


@pytest.mark.parametrize(
    "agent",
    [
        None,
        "",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "WhatsApp/2.23.20.0 A",
        "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
        "Twitterbot/1.0",
        "TelegramBot (like TwitterBot)",
        "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        "python-requests/2.31.0",
        "curl/8.4.0",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 HeadlessChrome/130.0 Safari/537.36",
    ],
)
def test_crawlers_link_previews_scripts_and_a_missing_agent_are_bots(agent):
    assert looks_like_bot(agent) is True
