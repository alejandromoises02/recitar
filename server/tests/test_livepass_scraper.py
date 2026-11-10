from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.scrapers.livepass import (
    BUENOS_AIRES,
    event_paths_from_listing,
    filter_regions,
    parse_event,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 8, tzinfo=BA)


def event(name: str):
    html = (FIXTURES / f"livepass_{name}.html").read_text(encoding="utf-8")
    return parse_event(html, NOW)


def test_event_fields():
    e = event("caba_malvinas")
    # Livepass titles are marketing text ("<ARTIST> en <place>"); kept verbatim for now.
    assert e.title.startswith("A PERFECT CIRCLE")
    assert e.artist is None  # not extracted yet: Livepass only publishes the marketing title
    assert e.venue == "Microestadio Malvinas Argentinas"
    assert e.category == "concert"
    assert e.starts_at.isoformat() == "2026-11-28T21:00:00-03:00"
    assert e.source_url.startswith("https://livepass.com.ar/events/")
    assert e.ticket_links[0].vendor == "Livepass"
    assert e.ticket_links[0].url.startswith("https://livepass.com.ar/events/")
    assert e.id.startswith("livepass-") and "20261128T2100" in e.id


def test_ciudad_is_recognised_by_region_or_comuna():
    # Livepass writes the region as "Ciudad Autónoma de Buenos Aires" for some venues
    # and just "Buenos Aires" for others; the "Comuna N" locality is the reliable hint.
    assert event("caba_malvinas").region == "AR-C"
    assert event("caba_uriarte").region == "AR-C"


def test_city_events_use_the_city_name_not_the_comuna():
    for name in ("caba_malvinas", "caba_uriarte"):
        assert event(name).city == "Buenos Aires"


def test_province_is_told_apart_from_the_city():
    # Same region text "Buenos Aires" as Uriarte, but a province locality.
    assert event("laplata_opera").region == "AR-B"
    assert event("provincia_hipodromo").region == "AR-B"
    assert event("provincia_hipodromo").city == "La Plata"


def test_other_provinces_keep_their_own_region():
    e = event("neuquen")
    assert e.country == "AR"
    assert e.region == "AR-Q"


def test_filter_keeps_only_requested_regions():
    events = [event(n) for n in ("caba_malvinas", "laplata_opera", "neuquen")]
    kept = filter_regions(events, BUENOS_AIRES)
    assert [e.region for e in kept] == ["AR-C", "AR-B"]


def test_past_events_are_dropped():
    html = (FIXTURES / "livepass_caba_malvinas.html").read_text(encoding="utf-8")
    assert parse_event(html, datetime(2027, 1, 1, tzinfo=BA)) is None


def test_page_without_event_data_yields_none():
    assert parse_event("<html><body>nothing</body></html>", NOW) is None


def test_listing_links_are_unique_event_paths():
    html = '<a href="/events/a">a</a><a href="/events/a">a</a><a href="/t/show">x</a><a href="/events/b">b</a>'
    assert event_paths_from_listing(html) == ["/events/a", "/events/b"]


def test_start_date_without_offset_is_read_as_buenos_aires_time():
    page = (
        '<script type="application/ld+json">{"@type":"Event","name":"X","url":"https://livepass.com.ar/events/x",'
        '"startDate":"2026-12-01T20:00","location":{"name":"V","address":{"addressCountry":"AR"}}}</script>'
    )
    assert parse_event(page, NOW).starts_at.isoformat() == "2026-12-01T20:00:00-03:00"


def test_image_comes_from_the_site_and_is_marked_as_source():
    e = event("caba_malvinas")
    assert e.image_url.startswith("https://livepass-com-ar.uploads.ticketplus.global/images/")
    assert e.image_origin == "source"


def test_stray_whitespace_in_the_title_is_collapsed():
    original = (FIXTURES / "livepass_caba_malvinas.html").read_text(encoding="utf-8")
    html = original.replace("A PERFECT CIRCLE", " A  PERFECT CIRCLE")
    assert html != original
    assert parse_event(html, NOW).title.startswith("A PERFECT CIRCLE")
