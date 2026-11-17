from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.domain.event import Event, TicketLink
from app.events_repository import (
    known_show_keys, list_featured_shows, list_just_announced_with_image, replace_featured, upsert_events,
)

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def event(id_: str, days: float, image: bool = True, seen_days_ago: float = 0, category: str = "concert") -> Event:
    return Event(
        id=id_, category=category, title=id_, venue="Niceto Club", starts_at=NOW + timedelta(days=days),
        ticket_links=[TicketLink(vendor="Venti", url="https://venti.live/x")], source_url="https://venti.live/x",
        updated_at=NOW, first_seen_at=NOW - timedelta(days=seen_days_ago),
        **({"image_url": f"/media/{id_}.webp", "image_origin": "licensed"} if image else {}),
    )


def test_the_migration_creates_the_featured_table(db_engine):
    columns = {c["name"] for c in inspect(db_engine).get_columns("featured_shows")}
    assert columns == {"show_key", "position"}


def test_known_show_keys_are_the_shows_stored_whole(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event("venti-a-20261120T2100", 12), event("venti-old-20261101T2100", -7)])
        found = known_show_keys(conn, ["venti-a", "venti-old", "venti", "venti-a-20261120T2100", "nope"])
    assert found == {"venti-a", "venti-old"}


def test_featured_shows_come_in_the_order_they_were_picked(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event("venti-a-20261120T2100", 12), event("venti-b-20261121T2100", 13)])
        replace_featured(conn, ["venti-b", "venti-a"])
        assert [s.id for s in list_featured_shows(conn, NOW, 10)] == ["venti-b", "venti-a"]


def test_picking_again_replaces_the_whole_list(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event("venti-a-20261120T2100", 12), event("venti-b-20261121T2100", 13)])
        replace_featured(conn, ["venti-a", "venti-b"])
        replace_featured(conn, ["venti-b"])
        assert [s.id for s in list_featured_shows(conn, NOW, 10)] == ["venti-b"]
        replace_featured(conn, [])
        assert list_featured_shows(conn, NOW, 10) == []


def test_featured_shows_without_upcoming_dates_or_an_image_are_left_out(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [
            event("venti-gone-20261101T2100", -7),
            event("venti-plain-20261120T2100", 12, image=False),
            event("venti-ok-20261121T2100", 13),
        ])
        replace_featured(conn, ["venti-gone", "venti-plain", "venti-ok"])
        assert [s.id for s in list_featured_shows(conn, NOW, 10)] == ["venti-ok"]


def test_featured_respects_the_limit(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event(f"venti-{i}-20261120T2100", 12) for i in range(3)])
        replace_featured(conn, ["venti-2", "venti-0", "venti-1"])
        assert [s.id for s in list_featured_shows(conn, NOW, 2)] == ["venti-2", "venti-0"]


def test_just_announced_with_image_is_newest_first_within_14_days(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [
            event("venti-new-20261120T2100", 12, seen_days_ago=1),
            event("venti-mid-20261121T2100", 13, seen_days_ago=5),
            event("venti-plain-20261122T2100", 14, image=False, seen_days_ago=0),
            event("venti-old-20261123T2100", 15, seen_days_ago=20),
        ])
        found = list_just_announced_with_image(conn, NOW, 10)
    assert [s.id for s in found] == ["venti-new", "venti-mid"]


def test_featured_and_just_announced_shows_can_be_of_one_kind_only(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event("venti-a-20261120T2100", 12), event("ticketek-play-20261121T2100", 13, category="theatre")])
        replace_featured(conn, ["ticketek-play", "venti-a"])
        assert [s.id for s in list_featured_shows(conn, NOW, 10, "concert")] == ["venti-a"]
        assert [s.id for s in list_featured_shows(conn, NOW, 10)] == ["ticketek-play", "venti-a"]
        assert [s.id for s in list_just_announced_with_image(conn, NOW, 10, "theatre")] == ["ticketek-play"]
