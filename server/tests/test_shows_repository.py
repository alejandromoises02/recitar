from datetime import datetime, timedelta, timezone

from app.domain.event import Event, TicketLink
from app.events_repository import EventFilters, list_upcoming_shows, upsert_events

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def event(id_: str, days: float, seen_days_ago: float = 0, **extra) -> Event:
    fields = dict(
        id=id_, category="concert", title="Divididos", venue="Movistar Arena", starts_at=NOW + timedelta(days=days),
        ticket_links=[TicketLink(vendor="Movistar Arena", url=f"https://t.example.com/{id_}")],
        source_url="https://example.com/show", updated_at=NOW, first_seen_at=NOW - timedelta(days=seen_days_ago),
    )
    return Event(**{**fields, **extra})


def shows(db_engine, stored: list[Event], *, limit: int = 50, after=None, sort="starts_at", **filters):
    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        return list_upcoming_shows(conn, NOW, limit, after, EventFilters(**filters), sort)


def test_the_dates_of_a_show_come_together_soonest_first_with_their_ticket_links(db_engine):
    stored = [
        event("movistar-divididos-20261125T2100", 17, title="Divididos (2da fecha)"),
        event("movistar-divididos-20261120T2100", 12),
        event("movistar-divididos-20261101T2100", -7),  # already happened
    ]
    (show,) = shows(db_engine, stored)
    assert show.id == "movistar-divididos"
    assert show.title == "Divididos"  # from the next date
    assert [(d.id, d.starts_at) for d in show.dates] == [
        ("movistar-divididos-20261120T2100", NOW + timedelta(days=12)),
        ("movistar-divididos-20261125T2100", NOW + timedelta(days=17)),
    ]
    assert show.dates[0].ticket_links == [
        TicketLink(vendor="Movistar Arena", url="https://t.example.com/movistar-divididos-20261120T2100")
    ]


def test_a_show_with_only_past_dates_is_left_out(db_engine):
    assert shows(db_engine, [event("venti-gone-20261101T2100", -7)]) == []


def test_shows_go_by_their_next_date_then_id_and_page_without_repeating(db_engine):
    stored = [
        event("venti-late-20261130T2100", 22),
        event("venti-b-20261115T2100", 7),
        event("venti-a-20261115T2100", 7),
        event("venti-a-20261201T2100", 23),
    ]
    first = shows(db_engine, stored, limit=2)
    rest = shows(db_engine, [], limit=2, after=(first[-1].dates[0].starts_at, first[-1].id))
    assert [s.id for s in first] == ["venti-a", "venti-b"]
    assert [s.id for s in rest] == ["venti-late"]


def test_the_show_key_is_compared_whole(db_engine):
    stored = [event("colon-cascanueces-20261120T2000", 12), event("colon-cascanueces-2-20261121T2000", 13)]
    found = shows(db_engine, stored)
    assert [(s.id, len(s.dates)) for s in found] == [("colon-cascanueces", 1), ("colon-cascanueces-2", 1)]


def test_a_show_is_listed_when_any_date_matches_and_brings_all_its_dates(db_engine):
    stored = [
        event("venti-x-20261110T2100", 2),
        event("venti-x-20261128T2100", 20),
        event("venti-y-20261110T2100", 2),
    ]
    (show,) = shows(db_engine, stored, starts_from=NOW + timedelta(days=15))
    assert show.id == "venti-x"
    assert [d.id for d in show.dates] == ["venti-x-20261110T2100", "venti-x-20261128T2100"]


def test_search_venue_and_category_also_pick_shows_by_their_dates(db_engine):
    stored = [
        event("venti-mila-20261120T2100", 12, title="Mila en Humboldt", venue="Niceto Club", category="party"),
        event("colon-aida-20261120T2000", 12, title="Aida", venue="Teatro Colón", category="theatre"),
    ]
    assert [s.id for s in shows(db_engine, stored, q="mila")] == ["venti-mila"]
    assert [s.id for s in shows(db_engine, [], venues=("Teatro Colón",))] == ["colon-aida"]
    assert [s.id for s in shows(db_engine, [], category="party")] == ["venti-mila"]


def test_a_show_is_first_seen_when_any_of_its_dates_was_even_a_past_one(db_engine):
    stored = [
        event("venti-old-20261101T2100", -7, seen_days_ago=40),
        event("venti-old-20261130T2100", 22, seen_days_ago=0),
    ]
    (show,) = shows(db_engine, stored)
    assert show.first_seen_at == NOW - timedelta(days=40)


def test_by_announcement_the_newest_show_comes_first_and_pages_by_id_on_ties(db_engine):
    stored = [
        event("venti-old-20261120T2100", 12, seen_days_ago=9),
        event("venti-b-20261125T2100", 17, seen_days_ago=1),
        event("venti-a-20261126T2100", 18, seen_days_ago=1),
        event("venti-a-20261127T2100", 19, seen_days_ago=0.5),
    ]
    first = shows(db_engine, stored, limit=2, sort="announced")
    rest = shows(db_engine, [], limit=2, sort="announced", after=(first[-1].first_seen_at, first[-1].id))
    assert [s.id for s in first] == ["venti-b", "venti-a"]
    assert [s.id for s in rest] == ["venti-old"]


def test_announced_from_looks_at_the_show_not_at_its_newest_date(db_engine):
    stored = [
        event("venti-old-20261120T2100", 12, seen_days_ago=30),
        event("venti-old-20261130T2100", 22, seen_days_ago=0),  # a new date of a show we knew
        event("venti-new-20261125T2100", 17, seen_days_ago=2),
    ]
    found = shows(db_engine, stored, announced_from=NOW - timedelta(days=14))
    assert [s.id for s in found] == ["venti-new"]


def test_a_show_carries_the_readable_name_of_its_next_date(db_engine):
    (show,) = shows(db_engine, [event("livepass-tb-20261120T2100", 12, title="TAN BIONICA en Estadio Uno")])
    assert (show.title, show.name) == ("TAN BIONICA en Estadio Uno", "Tan Bionica")


def one_show(db_engine, stored: list[Event], key: str):
    from app.events_repository import get_upcoming_show

    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        return get_upcoming_show(conn, key, NOW)


def test_one_show_comes_with_all_its_upcoming_dates_and_none_of_another_show(db_engine):
    stored = [
        event("movistar-divididos-20261125T2100", 17, updated_at=NOW - timedelta(hours=1)),
        event("movistar-divididos-20261120T2100", 12, updated_at=NOW - timedelta(hours=4)),
        event("movistar-divididos-20261101T2100", -7),  # already happened
        event("movistar-divididos-2-20261121T2100", 13),  # another show whose key starts the same
    ]
    show = one_show(db_engine, stored, "movistar-divididos")
    assert show is not None
    assert [d.id for d in show.dates] == ["movistar-divididos-20261120T2100", "movistar-divididos-20261125T2100"]
    assert show.updated_at == NOW - timedelta(hours=1)


def test_a_show_with_only_past_dates_or_no_dates_is_not_found(db_engine):
    stored = [event("movistar-ayer-20261101T2100", -7)]
    assert one_show(db_engine, stored, "movistar-ayer") is None
    assert one_show(db_engine, [], "movistar-nadie") is None
