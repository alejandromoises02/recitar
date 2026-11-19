"""One row per performance when two sources publish it.

A venue with its own scraper also sells through ticketers we read (the Colón through Ticketek and
TuEntrada), so the same performance arrives twice under different ids. Two events from different
sources at the same venue and the same date and time are one performance: one row is kept and the
other's ticket links are added to it. Titles differ between sources, so they are not compared.

Only events with a known time and a real venue are joined: a day-only date is that day's midnight,
and a placeholder venue is not a place. Two events of one source are never joined (Niceto's club
and bar rooms share a name and can share a time).
"""

from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

from app.domain.event import VENUE_TO_BE_CONFIRMED, Event, TicketLink

# A venue's own source has the best title and information for it, so its row is the one kept.
VENUE_SOURCES: dict[str, str] = {"Teatro Colón": "colon"}


def source_of(event_id: str) -> str:
    return event_id.split("-", 1)[0]


def merge_same_shows(incoming: list[Event], stored: list[Event]) -> tuple[list[Event], list[str]]:
    """Events to save (incoming ones in their order, then stored winners that gained links) and the
    ids of stored rows to delete. `stored` are the rows already saved at the venues and times of
    `incoming`; the kept row is the venue's own source, else a stored one, else the lowest id."""
    incoming_ids = {event.id for event in incoming}
    groups: dict[tuple[str, datetime], list[tuple[Event, bool]]] = defaultdict(list)
    for event in stored:
        if event.id not in incoming_ids and _joinable(event):
            groups[_slot(event)].append((event, True))
    for event in incoming:
        if _joinable(event):
            groups[_slot(event)].append((event, False))

    replaced: dict[str, Event] = {}
    dropped: set[str] = set()
    deleted: list[str] = []
    stored_winners: list[Event] = []
    for (venue, _), members in groups.items():
        winner, winner_stored = min(members, key=lambda member: _rank(venue, *member))
        losers = [(event, was_stored) for event, was_stored in members if source_of(event.id) != source_of(winner.id)]
        if not losers:
            continue
        merged = winner.model_copy(update={"ticket_links": _joined_links(winner, [event for event, _ in losers])})
        if winner_stored:
            stored_winners.append(merged)
        else:
            replaced[winner.id] = merged
        for event, was_stored in losers:
            if was_stored:
                deleted.append(event.id)
            else:
                dropped.add(event.id)

    saved = [replaced.get(event.id, event) for event in incoming if event.id not in dropped]
    return saved + stored_winners, sorted(deleted)


def _joinable(event: Event) -> bool:
    return event.time_known and event.venue != VENUE_TO_BE_CONFIRMED


def _slot(event: Event) -> tuple[str, datetime]:
    return event.venue, event.starts_at


def _rank(venue: str, event: Event, was_stored: bool) -> tuple[bool, bool, str]:
    return source_of(event.id) != VENUE_SOURCES.get(venue), not was_stored, event.id


def _joined_links(winner: Event, losers: list[Event]) -> list[TicketLink]:
    links = list(winner.ticket_links)
    seen = {_link_key(link.url) for link in links}
    for event in losers:
        for link in event.ticket_links:
            if _link_key(link.url) not in seen:
                seen.add(_link_key(link.url))
                links.append(link)
    return links


def _link_key(url: str) -> tuple[str, str, str]:
    """A link compared without its scheme, `www.` or trailing slash."""
    parts = urlparse(url)
    return (parts.hostname or "").removeprefix("www."), parts.path.rstrip("/"), parts.query
