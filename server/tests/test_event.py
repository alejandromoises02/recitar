from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.event import Event, TicketLink


def make_event(**overrides):
    data = dict(
        id="colon-un-sueno-navideno-2026-12-19T15:00",
        category="concert",
        title="Un sueño navideño",
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


def test_artist_is_optional_and_empty_by_default():
    assert make_event().artist is None
    assert make_event(artist="Abel Pintos").artist == "Abel Pintos"


def test_title_is_required():
    data = make_event().model_dump()
    del data["title"]
    with pytest.raises(ValidationError):
        Event(**data)


def test_event_accepts_every_planned_category():
    for category in ("concert", "theatre", "party", "other"):
        assert make_event(category=category).category == category


def test_event_rejects_unknown_category():
    with pytest.raises(ValidationError):
        make_event(category="sports")


def test_event_requires_timezone_aware_start():
    with pytest.raises(ValidationError):
        make_event(starts_at=datetime(2026, 12, 19, 15, 0))


def test_images_are_empty_by_default():
    e = make_event()
    assert (e.image_url, e.image_origin, e.image_author, e.image_license, e.image_source_url) == (None,) * 5


def test_image_origin_is_required_with_an_image():
    # The origin is what tells a hotlinked source image from a licensed copy, so it cannot be omitted.
    with pytest.raises(ValidationError):
        make_event(image_url="https://x.com/a.jpg")


def test_image_origin_needs_an_image():
    with pytest.raises(ValidationError):
        make_event(image_origin="source")


def test_image_origin_accepts_only_known_values():
    for origin in ("source", "licensed", "venue"):
        assert make_event(image_url="https://x.com/a.jpg", image_origin=origin).image_origin == origin
    with pytest.raises(ValidationError):
        make_event(image_url="https://x.com/a.jpg", image_origin="stolen")
