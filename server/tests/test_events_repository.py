from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.domain.event import Event, TicketLink
from app.events_repository import (
    EventFilters,
    count_upcoming_by_source,
    get_event,
    list_events,
    list_show_dates,
    list_upcoming,
    upsert_events,
)

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


def test_upcoming_events_are_paged_by_start_date_then_id_from_now_on(db_engine):
    past = event("venti-old-20261101T2100", starts_at=NOW - timedelta(days=1))
    a = event("venti-a-20261120T2100", starts_at=NOW + timedelta(days=2))
    b = event("venti-b-20261120T2100", starts_at=NOW + timedelta(days=2))
    later = event("venti-c-20261125T2100", starts_at=NOW + timedelta(days=3))
    with db_engine.begin() as conn:
        upsert_events(conn, [later, b, past, a])
    with db_engine.connect() as conn:
        first = list_upcoming(conn, NOW, limit=2, after=None)
        rest = list_upcoming(conn, NOW, limit=2, after=(first[-1].starts_at, first[-1].id))
    assert [e.id for e in first] == [a.id, b.id]
    assert [e.id for e in rest] == [later.id]


def search(db_engine, q: str, stored: list[Event]) -> list[str]:
    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        return [e.id for e in list_upcoming(conn, NOW, limit=50, after=None, filters=EventFilters(q=q))]


def test_search_ignores_case_and_accents(db_engine):
    stored = [event("movistar-mb-20261120T2100", title="María Becerra"), event("movistar-dv-20261120T2100", title="Divididos")]
    assert search(db_engine, "maria BECERRA", stored) == ["movistar-mb-20261120T2100"]


def test_search_matches_accented_words_from_a_plain_query_and_the_other_way_round(db_engine):
    stored = [event("venti-n-20261120T2100", title="Noche de ÑANDÚ"), event("venti-o-20261120T2100", title="Otra")]
    assert search(db_engine, "nandu", stored) == ["venti-n-20261120T2100"]
    assert search(db_engine, "ñandú", stored) == ["venti-n-20261120T2100"]


def test_every_word_must_appear_in_any_order(db_engine):
    stored = [
        event("venti-a-20261120T2100", title="Mila en Humboldt"),
        event("venti-b-20261120T2100", title="Mila en Niceto Bar"),
    ]
    assert search(db_engine, "humboldt mila", stored) == ["venti-a-20261120T2100"]


def test_search_also_looks_at_the_artist(db_engine):
    stored = [event("livepass-x-20261120T2100", title="Gira 2026 en Buenos Aires", artist="A Perfect Circle")]
    assert search(db_engine, "perfect circle", stored) == ["livepass-x-20261120T2100"]


def test_search_also_looks_at_the_venue(db_engine):
    stored = [
        event("venti-h-20261120T2100", title="Mila", venue="Humboldt | Niceto Club"),
        event("venti-k-20261120T2100", title="Otra", venue="Teatro Colón"),
    ]
    assert search(db_engine, "niceto", stored) == ["venti-h-20261120T2100"]
    assert search(db_engine, "mila niceto", stored) == ["venti-h-20261120T2100"]


def test_like_wildcards_in_the_query_are_plain_characters(db_engine):
    stored = [
        event("venti-p-20261120T2100", title="2x1 al 50% off"),
        event("venti-q-20261120T2100", title="Show_raro"),
        event("venti-r-20261120T2100", title="Showxraro"),
    ]
    assert search(db_engine, "50%", stored) == ["venti-p-20261120T2100"]
    assert search(db_engine, "%", stored) == ["venti-p-20261120T2100"]
    assert search(db_engine, "w_r", stored) == ["venti-q-20261120T2100"]


def test_search_without_matches_is_empty_and_past_events_never_match(db_engine):
    stored = [event("venti-old-20261101T2100", title="Divididos", starts_at=NOW - timedelta(days=1))]
    assert search(db_engine, "divididos", stored) == []
    assert search(db_engine, "nadie", stored) == []


def test_search_results_page_with_the_cursor_too(db_engine):
    stored = [
        event(f"venti-m{i}-20261120T2100", title=f"Mila {i}", starts_at=NOW + timedelta(days=i + 1)) for i in range(3)
    ] + [event("venti-z-20261120T2100", title="Otro", starts_at=NOW + timedelta(days=1, hours=1))]
    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        first = list_upcoming(conn, NOW, limit=2, after=None, filters=EventFilters(q="mila"))
        rest = list_upcoming(conn, NOW, limit=2, after=(first[-1].starts_at, first[-1].id), filters=EventFilters(q="mila"))
    assert [e.id for e in first + rest] == ["venti-m0-20261120T2100", "venti-m1-20261120T2100", "venti-m2-20261120T2100"]


def test_the_time_window_includes_its_start_and_excludes_its_end(db_engine):
    start, end = NOW + timedelta(days=1), NOW + timedelta(days=2)
    stored = [
        event("venti-before-20261109T1159", starts_at=start - timedelta(minutes=1)),
        event("venti-start-20261109T1200", starts_at=start),
        event("venti-last-20261110T1159", starts_at=end - timedelta(minutes=1)),
        event("venti-end-20261110T1200", starts_at=end),
    ]
    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        found = list_upcoming(conn, NOW, limit=50, after=None, filters=EventFilters(starts_from=start, starts_before=end))
    assert [e.id for e in found] == ["venti-start-20261109T1200", "venti-last-20261110T1159"]


def test_one_event_is_read_by_id_and_a_missing_one_is_none(db_engine):
    with db_engine.begin() as conn:
        upsert_events(conn, [event()])
    with db_engine.connect() as conn:
        assert get_event(conn, event().id) == event()
        assert get_event(conn, "movistar-nope-20261120T2100") is None


def test_the_upcoming_dates_of_a_show_are_its_own_and_not_those_of_a_show_with_a_longer_name(db_engine):
    day = timedelta(days=1)
    stored = [
        event("colon-el-cascanueces-20261101T2000", starts_at=NOW - day),  # already happened
        event("colon-el-cascanueces-20261120T2000", starts_at=NOW + 3 * day),
        event("colon-el-cascanueces-20261118T2000", starts_at=NOW + 2 * day),
        event("colon-el-cascanueces-2-20261119T2000", starts_at=NOW + 2 * day),  # another show
        event("colon-otra-20261118T2000", starts_at=NOW + 2 * day),
    ]
    with db_engine.begin() as conn:
        upsert_events(conn, stored)
    with db_engine.connect() as conn:
        dates = list_show_dates(conn, "colon-el-cascanueces", NOW)
    assert [d.id for d in dates] == ["colon-el-cascanueces-20261118T2000", "colon-el-cascanueces-20261120T2000"]
    assert dates[0].starts_at == NOW + 2 * day
