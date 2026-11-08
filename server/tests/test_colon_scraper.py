from datetime import datetime, timezone
from pathlib import Path

from app.scrapers.colon import parse_production

FIXTURE = Path(__file__).parent / "fixtures" / "colon_production.html"
URL = "https://teatrocolon.org.ar/produccion/un-sueno-navideno/"
NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)


def parse():
    return parse_production(FIXTURE.read_text(encoding="utf-8"), URL, NOW)


def test_one_event_per_performance():
    events = parse()
    assert len(events) == len(set(e.starts_at for e in events)) > 0


def test_first_performance_fields():
    first = parse()[0]
    assert first.artist == "Un sueño navideño"
    assert first.venue == "Teatro Colón"
    assert first.starts_at.isoformat() == "2026-12-19T15:00:00-03:00"
    assert first.source_url == URL
    assert first.ticket_links[0].vendor == "Entradas BA"
    assert first.ticket_links[0].url.startswith("https://entradasba.buenosaires.gob.ar/evento/")


def test_ids_are_stable_and_unique():
    ids = [e.id for e in parse()]
    assert len(ids) == len(set(ids))
    assert ids == [e.id for e in parse()]
