from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.event import Event, TicketLink


def make_event(**overrides):
    data = dict(
        id="colon-un-sueno-navideno-2026-12-19T15:00",
        category="concert",
        artist="Un sueño navideño",
        venue="Teatro Colón",
        starts_at=datetime(2026, 12, 19, 18, 0, tzinfo=timezone.utc),
        ticket_links=[TicketLink(vendor="Entradas BA", url="https://entradasba.buenosaires.gob.ar/evento/x")],
        source_url="https://teatrocolon.org.ar/produccion/un-sueno-navideno/",
        updated_at=datetime(2026, 11, 8, tzinfo=timezone.utc),
    )
    data.update(overrides)
    return Event(**data)


def test_event_accepts_valid_data():
    assert make_event().venue == "Teatro Colón"


def test_event_rejects_unknown_category():
    with pytest.raises(ValidationError):
        make_event(category="sports")


def test_event_requires_timezone_aware_start():
    with pytest.raises(ValidationError):
        make_event(starts_at=datetime(2026, 12, 19, 15, 0))
