import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.scrapers.venti import (
    event_urls_from_sitemap,
    filter_venue,
    parse_event,
)

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 8, tzinfo=BA)


def event(name: str):
    return parse_event((FIXTURES / f"venti_{name}.html").read_text(encoding="utf-8"), NOW)


def test_event_fields():
    e = event("humboldt")
    assert e.title.startswith("Mila en Humboldt")
    assert e.artist is None
    assert e.venue == "Humboldt | Niceto Club"
    assert e.source_url == "https://venti.live/evento/mila-en-humboldt-niceto-club"
    assert e.ticket_links[0].vendor == "Venti"
    assert e.ticket_links[0].url == e.source_url
    assert e.id == "venti-mila-en-humboldt-niceto-club-20261113T2100"


def test_utc_start_is_converted_to_buenos_aires_time():
    # Venti publishes 2026-11-14T00:00:00.000Z, which is 21:00 on the 13th in Buenos Aires.
    assert event("humboldt").starts_at.isoformat() == "2026-11-13T21:00:00-03:00"


def test_location_fields_match_the_other_sources():
    e = event("humboldt")
    assert (e.city, e.region, e.country) == ("Buenos Aires", "AR-C", "AR")


def test_locality_is_used_when_the_page_has_no_region():
    e = event("other")
    assert (e.city, e.region, e.country) == ("Mendoza", "AR-M", "AR")


def test_filter_by_venue_name():
    events = [event("humboldt"), event("niceto"), event("other")]
    kept = filter_venue(events, "niceto")
    assert [e.venue for e in kept] == ["Humboldt | Niceto Club", "Niceto Club"]
    assert filter_venue(events, None) == events


def test_past_events_are_dropped():
    html = (FIXTURES / "venti_humboldt.html").read_text(encoding="utf-8")
    assert parse_event(html, datetime(2027, 1, 1, tzinfo=BA)) is None


def test_page_without_event_data_yields_none():
    assert parse_event("<html><body>nothing</body></html>", NOW) is None


def test_sitemap_urls_keep_only_events_matching_the_hint():
    xml = (
        "<urlset>"
        "<url><loc>https://venti.live/eventos</loc></url>"
        "<url><loc>https://venti.live/evento/kybba-en-niceto-club-18-a-os</loc></url>"
        "<url><loc>https://venti.live/evento/otro-show-en-mendoza</loc></url>"
        "<url><loc>https://venti.live/organizadores/niceto</loc></url>"
        "</urlset>"
    )
    assert event_urls_from_sitemap(xml, "niceto") == ["https://venti.live/evento/kybba-en-niceto-club-18-a-os"]
    assert len(event_urls_from_sitemap(xml, None)) == 2


def _page(title: str, start_utc: str) -> str:
    return (
        '<script type="application/ld+json">'
        + json.dumps(
            {
                "@type": "Event",
                "name": title,
                "url": "https://venti.live/evento/x",
                "startDate": start_utc,
                "location": {"name": "Niceto Club", "address": {"addressLocality": "Buenos Aires", "addressCountry": "AR"}},
            }
        )
        + "</script>"
    )


def test_evening_show_is_provisionally_a_concert():
    # 2026-11-14T00:00Z is 21:00 in Buenos Aires
    assert event("humboldt").category == "concert"


def test_midnight_start_is_not_taken_for_a_concert():
    # Kybba starts at 23:59 and ends at dawn: an all-night event, kept out of "concert".
    assert event("niceto").category == "other"


def test_party_words_in_the_title_keep_it_out_of_concerts():
    for title in ("La Chicle - Fiesta Disco en Niceto Bar", "NOCHE PANTERA en Niceto Bar", "TRASNOCHE en Niceto"):
        assert parse_event(_page(title, "2026-11-14T00:00:00.000Z"), NOW).category == "other"


def test_image_comes_from_the_site_and_is_marked_as_source():
    e = event("humboldt")
    assert e.image_url == "https://images.venti.live/user-images/1780489377566-lg.jpg"
    assert e.image_origin == "source"


def test_event_without_an_image_has_no_origin_either():
    e = event("niceto")
    assert (e.image_url, e.image_origin) == (None, None)


def test_stray_whitespace_in_the_title_is_collapsed():
    original = (FIXTURES / "venti_humboldt.html").read_text(encoding="utf-8")
    html = original.replace("Mila en Humboldt", " Mila  en  Humboldt")
    assert html != original
    assert parse_event(html, NOW).title.startswith("Mila en Humboldt")


def test_a_start_date_without_a_time_has_the_time_unknown():
    e = parse_event(_page("Show", "2026-12-01"), NOW)
    assert e.starts_at.isoformat() == "2026-12-01T00:00:00-03:00"
    assert e.time_known is False


def test_a_start_date_with_a_time_has_the_time_known():
    assert event("humboldt").time_known is True
