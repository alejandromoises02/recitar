from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.scrapers.movistar import parse_show, shows_from_listing

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 8, tzinfo=BA)


def show(name: str, now: datetime = NOW):
    return parse_show((FIXTURES / f"movistar_show_{name}.html").read_text(encoding="utf-8"), now)


def test_listing_gives_one_path_per_show():
    html = (FIXTURES / "movistar_listing.html").read_text(encoding="utf-8")
    paths = shows_from_listing(html)
    assert len(paths) == len(set(paths)) == 5
    assert all(p.startswith("/show/") for p in paths)


def test_a_multi_date_show_gives_one_event_per_date():
    events = show("multi")
    assert len(events) == 9
    assert len({e.id for e in events}) == 9


def test_event_fields():
    first = show("multi")[0]
    assert first.title == "María Becerra"
    assert first.artist is None
    assert first.category == "concert"
    assert first.venue == "Movistar Arena"
    assert first.starts_at.isoformat() == "2026-11-13T21:00:00-03:00"
    assert (first.city, first.region, first.country) == ("Buenos Aires", "AR-C", "AR")
    assert first.source_url.startswith("https://www.movistararena.com.ar/show/")
    assert first.ticket_links[0].vendor == "Movistar Arena"
    assert first.ticket_links[0].url == first.source_url
    assert first.id == "movistar-993a2d46-39d7-4455-b199-87a5a2dc9b83-20261113T2100"


def test_a_single_date_show_is_read_too():
    # One date: Movistar publishes the JSON-LD as an object instead of a list
    events = show("single")
    assert len(events) == 1
    assert events[0].starts_at.isoformat() == "2026-11-08T21:00:00-03:00"


def test_party_in_the_title_is_not_a_concert():
    assert show("single")[0].category == "other"


def test_two_shows_on_the_same_day_keep_their_own_time():
    events = show("same_day")
    assert [e.starts_at.strftime("%H:%M") for e in events] == ["15:00", "20:00"]
    assert len({e.id for e in events}) == 2


def test_past_dates_are_dropped():
    later = datetime(2026, 11, 16, tzinfo=BA)
    events = show("multi", later)
    assert len(events) == 6 and all(e.starts_at >= later for e in events)


def test_page_without_event_data_yields_nothing():
    assert parse_show("<html><body>nothing</body></html>", NOW) == []


def test_movistars_own_image_is_not_used():
    # Its terms forbid reproducing its content, so images come from the alternative plan instead.
    assert all((e.image_url, e.image_origin) == (None, None) for e in show("multi"))


def test_stray_whitespace_in_the_title_is_collapsed():
    original = (FIXTURES / "movistar_show_multi.html").read_text(encoding="utf-8")
    html = original.replace('"Mar\\u00eda Becerra"', '" Mar\\u00eda  Becerra "')
    assert html != original  # the fixture escapes the accent; make sure the padding really went in
    assert parse_show(html, NOW)[0].title == "María Becerra"
