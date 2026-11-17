import logging
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.scrapers.colon import parse_calendar

FIXTURES = Path(__file__).parent / "fixtures"
BA = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 8, 0, 0, tzinfo=BA)


def calendar(month: int):
    html = (FIXTURES / f"colon_calendar_2026_{month:02d}.html").read_text(encoding="utf-8")
    return parse_calendar(html, 2026, month, NOW)


def test_counts_match_what_the_site_shows():
    assert len(calendar(11)) == 24
    assert len(calendar(12)) == 21


def test_performance_with_tickets():
    manon = calendar(11)[0]
    assert manon.title == "Manon"
    assert manon.artist is None
    assert manon.venue == "Teatro Colón"
    assert manon.category == "theatre"
    assert manon.starts_at.isoformat() == "2026-11-08T17:00:00-03:00"
    assert manon.source_url == "https://teatrocolon.org.ar/produccion/manon/"
    assert manon.ticket_links[0].vendor == "Entradas BA"
    assert manon.ticket_links[0].url.startswith("https://entradasba.buenosaires.gob.ar/evento/")


def test_location_fields_are_filled_like_every_other_source():
    manon = calendar(11)[0]
    assert (manon.city, manon.region, manon.country) == ("Buenos Aires", "AR-C", "AR")


def test_free_performance_has_no_ticket_links():
    free = [e for e in calendar(11) if e.title == "Cartografía del poder"]
    assert len(free) == 1
    assert free[0].ticket_links == []


def test_music_category_is_a_concert():
    cats = {e.title: e.category for e in calendar(11)}
    assert cats["Mozart y Beethoven: obras para clarinete y cuerdas"] == "concert"


def test_same_day_performances_keep_their_own_time():
    day15 = [e for e in calendar(11) if e.starts_at.day == 15]
    assert len(day15) == 4
    assert len({e.id for e in day15}) == 4


def test_ids_are_unique_and_stable_across_months():
    ids = [e.id for e in calendar(11) + calendar(12)]
    assert len(ids) == len(set(ids))
    assert ids == [e.id for e in calendar(11) + calendar(12)]


def test_past_performances_are_dropped():
    later = datetime(2026, 11, 20, tzinfo=BA)
    html = (FIXTURES / "colon_calendar_2026_11.html").read_text(encoding="utf-8")
    events = parse_calendar(html, 2026, 11, later)
    assert events and all(e.starts_at >= later for e in events)


def test_page_without_calendar_items_yields_nothing():
    assert parse_calendar("<html><body>nothing</body></html>", 2026, 11, NOW) == []


def test_image_comes_from_the_site_and_is_marked_as_source():
    manon = calendar(11)[0]
    assert manon.image_url == "https://teatrocolon.org.ar/wp-content/uploads/2025/12/Manon_tapa-redes_web-1.png"
    assert manon.image_origin == "source"


def relabelled(label: str) -> list:
    """The November calendar with every performance under one program label."""
    html = (FIXTURES / "colon_calendar_2026_11.html").read_text(encoding="utf-8")
    html, count = re.subn(r'class="category">[^<]*<', f'class="category">{label}<', html)
    assert count > 0
    return parse_calendar(html, 2026, 11, NOW)


@pytest.mark.parametrize("label, category", [
    ("Fuera de Ciclo", "concert"),  # Bach: Tres Conciertos de Brandeburgo
    ("Grandes Intérpretes", "concert"),
    ("Contemporáneo", "concert"),
    ("Orquesta Académica del Teatro Colón", "concert"),
    ("Colón para niños", "theatre"),  # family shows, as in the other sources
    ("CETC", "other"),
    ("Temporada 2026", "other"),  # guided visits
    ("Ópera", "theatre"),
    ("Música de Cámara", "concert"),
])
def test_each_program_label_maps_to_a_category(label, category, caplog):
    assert {e.category for e in relabelled(label)} == {category}
    assert caplog.records == []  # every one of these is known


def test_an_unknown_program_label_is_other_and_logged(caplog):
    with caplog.at_level(logging.WARNING):
        assert {e.category for e in relabelled("Ciclo Nuevo")} == {"other"}
    assert [r.getMessage() for r in caplog.records] == ['Teatro Colón program label not mapped: "Ciclo Nuevo"']
