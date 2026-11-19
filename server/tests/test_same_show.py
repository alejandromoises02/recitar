from datetime import datetime, timedelta, timezone

from app.domain.event import VENUE_TO_BE_CONFIRMED, Event, TicketLink
from app.domain.same_show import merge_same_shows

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
AT = NOW + timedelta(days=24)


def event(id_: str, venue: str = "Teatro Colón", starts_at: datetime = AT, links: list[tuple[str, str]] | None = None, **extra) -> Event:
    fields = dict(
        id=id_, category="concert", title=id_.split("-")[1], venue=venue, city="Buenos Aires",
        region="AR-C", country="AR", starts_at=starts_at,
        ticket_links=[TicketLink(vendor=v, url=u) for v, u in (links or [])],
        source_url=f"https://example.com/{id_}", updated_at=NOW,
    )
    return Event(**{**fields, **extra})


COLON = event("colon-walsh-20261202T1500", links=[("Ticketek", "https://www.ticketek.com.ar/walsh/teatro-colon")])
TICKETEK = event("ticketek-walsh-sinfonico-20261202T1500", links=[("Ticketek", "https://www.ticketek.com.ar/walsh/teatro-colon")])


def test_two_sources_with_the_same_venue_and_time_keep_one_row():
    saved, deleted = merge_same_shows([COLON, TICKETEK], stored=[])
    assert [e.id for e in saved] == [COLON.id]
    assert deleted == []


def test_the_venue_own_source_wins_whatever_the_order():
    saved, _ = merge_same_shows([TICKETEK, COLON], stored=[])
    assert [e.id for e in saved] == [COLON.id]


def test_a_link_already_there_is_not_repeated_even_with_another_scheme_or_www():
    colon = event("colon-gismonti-20261121T1700", links=[("TuEntrada", "http://tuentrada.com/egberto-gismonti-tc")])
    tuentrada = event("tuentrada-gismonti-tc-20261121T1700", links=[("TuEntrada", "https://www.tuentrada.com/egberto-gismonti-tc/")])
    (saved,), _ = merge_same_shows([colon, tuentrada], stored=[])
    assert saved.ticket_links == colon.ticket_links


def test_links_the_winner_lacks_are_added_after_its_own():
    ticketek = event("ticketek-walsh-20261202T1500", links=[("Ticketek", "https://www.ticketek.com.ar/otro")])
    (saved,), _ = merge_same_shows([COLON, ticketek], stored=[])
    assert [link.url for link in saved.ticket_links] == [
        "https://www.ticketek.com.ar/walsh/teatro-colon", "https://www.ticketek.com.ar/otro",
    ]


def test_a_stored_duplicate_is_deleted_when_the_winner_arrives():
    saved, deleted = merge_same_shows([COLON], stored=[TICKETEK])
    assert [e.id for e in saved] == [COLON.id]
    assert deleted == [TICKETEK.id]


def test_a_stored_winner_keeps_its_row_and_gains_the_new_links():
    ticketek = event("ticketek-walsh-20261202T1500", links=[("Ticketek", "https://www.ticketek.com.ar/otro")])
    (saved,), deleted = merge_same_shows([ticketek], stored=[COLON])
    assert saved.id == COLON.id
    assert [link.url for link in saved.ticket_links][-1] == "https://www.ticketek.com.ar/otro"
    assert deleted == []


def test_without_the_venue_own_source_the_stored_row_wins():
    stored = event("livepass-x-20261205T2100", venue="Teatro Ópera", links=[("Livepass", "https://livepass.com.ar/x")])
    new = event("ticketek-x-20261205T2100", venue="Teatro Ópera", links=[("Ticketek", "https://ticketek.com.ar/x")])
    (saved,), deleted = merge_same_shows([new], stored=[stored])
    assert saved.id == stored.id
    assert deleted == []


def test_the_stored_copy_of_an_incoming_event_is_not_its_own_duplicate():
    saved, deleted = merge_same_shows([COLON], stored=[COLON])
    assert saved == [COLON]
    assert deleted == []


def test_same_source_at_the_same_venue_and_time_is_two_shows():
    club = event("venti-a-20261121T0000", venue="Niceto Club")
    bar = event("venti-b-20261121T0000", venue="Niceto Club")
    saved, _ = merge_same_shows([club, bar], stored=[])
    assert saved == [club, bar]


def test_other_times_or_venues_are_left_alone():
    later = event("ticketek-walsh-20261202T2000", starts_at=AT + timedelta(hours=5))
    elsewhere = event("ticketek-walsh-sinfonico-teatro-opera-20261202T1500", venue="Teatro Ópera")
    saved, _ = merge_same_shows([COLON, later, elsewhere], stored=[])
    assert saved == [COLON, later, elsewhere]


def test_shows_without_a_known_time_or_venue_are_never_joined():
    day_only = [event("colon-a-20261202T0000", time_known=False), event("ticketek-b-20261202T0000", time_known=False)]
    unknown_venue = [
        event("enigma-a-20261202T1500", venue=VENUE_TO_BE_CONFIRMED),
        event("ticketek-b-20261202T1500", venue=VENUE_TO_BE_CONFIRMED),
    ]
    saved, _ = merge_same_shows(day_only + unknown_venue, stored=[])
    assert saved == day_only + unknown_venue
