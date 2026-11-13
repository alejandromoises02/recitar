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


def test_start_time_is_written_in_buenos_aires_time_and_reads_back_as_the_same_instant():
    from datetime import datetime, timezone

    from app.domain.event import Event, TicketLink

    utc = datetime(2026, 11, 15, 1, 0, tzinfo=timezone.utc)
    e = Event(
        id="x", category="concert", title="T", venue="V", starts_at=utc,
        ticket_links=[TicketLink(vendor="X", url="https://x.com")], source_url="https://x.com", updated_at=utc,
    )
    dumped = e.model_dump(mode="json")
    assert dumped["starts_at"] == "2026-11-14T22:00:00-03:00"
    assert Event.model_validate(dumped) == e


def test_first_seen_defaults_to_the_time_the_scraper_read_it():
    assert make_event().first_seen_at == datetime(2026, 11, 8, tzinfo=timezone.utc)


def test_an_explicit_first_seen_is_kept():
    earlier = datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert make_event(first_seen_at=earlier).first_seen_at == earlier


def test_first_seen_must_carry_a_time_zone():
    with pytest.raises(ValidationError):
        make_event(first_seen_at=datetime(2026, 10, 1))


def test_the_name_is_the_tidy_title_for_its_source():
    shouted = make_event(id="livepass-tan-bionica-20261120T2100", title="TAN BIONICA en Estadio Uno")
    assert shouted.name == "Tan Bionica"
    assert shouted.title == "TAN BIONICA en Estadio Uno"  # the source's words stay as they were


def test_the_name_is_sent_with_the_event():
    assert make_event().model_dump(mode="json")["name"] == "Un sueño navideño"
