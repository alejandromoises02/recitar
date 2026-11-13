from datetime import datetime, timezone

from app.domain.event import Event, TicketLink
from app.pipeline import add_artists

NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)


def event(id_: str, title: str, artist: str | None = None) -> Event:
    return Event(
        id=id_, category="concert", title=title, artist=artist, venue="X", starts_at=NOW,
        ticket_links=[TicketLink(vendor="V", url="https://v.example")], source_url="https://v.example", updated_at=NOW,
    )


def test_an_empty_artist_is_read_from_the_title():
    (found,) = add_artists([event("livepass-ed-20261120T2100", "ED SHEERAN en Huracan")])
    assert found.artist == "Ed Sheeran"


def test_an_artist_the_source_gave_is_kept():
    (found,) = add_artists([event("livepass-ed-20261120T2100", "ED SHEERAN en Huracan", artist="Edward Sheeran")])
    assert found.artist == "Edward Sheeran"


def test_when_the_title_does_not_say_the_artist_stays_empty():
    (found,) = add_artists([event("colon-cascanueces-20261120T2000", "El cascanueces")])
    assert found.artist is None


def test_nothing_else_changes_and_the_order_is_kept():
    items = [event("venti-a-20261120T2100", "NOCHE PANTERA en Niceto Bar"), event("movistar-b-20261121T2100", "Slayer")]
    found = add_artists(items)
    assert [e.id for e in found] == ["venti-a-20261120T2100", "movistar-b-20261121T2100"]
    assert [e.model_dump(exclude={"artist"}) for e in found] == [e.model_dump(exclude={"artist"}) for e in items]
