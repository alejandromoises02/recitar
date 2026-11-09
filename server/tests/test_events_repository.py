from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.domain.event import Event, TicketLink
from app.events_repository import count_upcoming_by_source, list_events, upsert_events

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def event(id_: str = "movistar-a-20261120T2100", **extra) -> Event:
    fields = dict(
        id=id_, category="concert", title="Divididos", venue="Movistar Arena", city="Buenos Aires",
        region="AR-C", country="AR", starts_at=NOW + timedelta(days=12),
        ticket_links=[TicketLink(vendor="Movistar Arena", url="https://t.example.com/1")],
        source_url="https://example.com/show/1", updated_at=NOW,
    )
    return Event(**{**fields, **extra})


def test_the_migration_creates_the_events_table(db_engine):
    columns = {c["name"] for c in inspect(db_engine).get_columns("events")}
    assert {"id", "title", "starts_at", "ticket_links", "image_origin", "image_license", "updated_at"} <= columns


def test_events_come_back_as_they_went_in(db_engine):
    licensed = event(
        "movistar-b-20261121T2100", image_url="/media/x.webp", image_origin="licensed", image_author="Elemaki",
        image_license="CC BY 3.0", image_source_url="https://commons.wikimedia.org/wiki/File:Divididos.JPG",
    )
    with db_engine.begin() as conn:
        upsert_events(conn, [event(), licensed])
    with db_engine.connect() as conn:
        stored = list_events(conn)
    assert stored == [event(), licensed]


def test_saving_the_same_event_again_updates_it_instead_of_duplicating(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event()])
        upsert_events(conn, [event(title="Divididos (nueva fecha)", updated_at=NOW + timedelta(days=1))])
    with db_engine.connect() as conn:
        (stored,) = list_events(conn)
    assert stored.title == "Divididos (nueva fecha)"
    assert stored.updated_at == NOW + timedelta(days=1)


def test_saving_nothing_is_fine(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [])
        assert list_events(conn) == []


def test_upcoming_events_are_counted_per_source(db_engine):
    items = [
        event("movistar-a-20261120T2100", starts_at=NOW + timedelta(days=12)),
        event("movistar-b-20261121T2100", starts_at=NOW + timedelta(days=13)),
        event("venti-c-20261122T2100", starts_at=NOW + timedelta(days=14)),
        event("venti-old-20260101T2100", starts_at=NOW - timedelta(days=30)),  # already happened
    ]
    with db_engine.begin() as conn:
        upsert_events(conn, items)
        assert count_upcoming_by_source(conn, NOW) == {"movistar": 2, "venti": 1}


def test_events_are_listed_by_start_date(db_engine):
    late = event("movistar-late-20261201T2100", starts_at=NOW + timedelta(days=30))
    soon = event("movistar-soon-20261115T2100", starts_at=NOW + timedelta(days=7))
    with db_engine.begin() as conn:
        upsert_events(conn, [late, soon])
        assert [e.id for e in list_events(conn)] == [soon.id, late.id]
