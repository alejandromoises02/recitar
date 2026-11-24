"""One command for the whole trip: scrape every source, choose each event's image, store them.

    python -m app.run                   # all sources
    python -m app.run --only colon,venti

A source that fails is reported and skipped; the others still run. Events already stored are
updated, not duplicated. Events that a site stops listing are not removed (yet). The first time a
source is read, its shows were already on sale: they are stored as seen before we started watching,
so they do not flood "just announced".
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Collection, Mapping

from app.db import make_engine, migrate
from app.domain.event import Event
from app.events_repository import count_upcoming_by_source, stored_sources, upsert_events
from app.images.copy import IMAGES_DIR, LocalImageStore
from app.images.wikimedia import MissingContactError, user_agent
from app.pipeline import add_artists, enrich_images
from app.scrapers import allaccess, articket, colon, coolco, enigma, granrivadavia, livepass, movistar, pulso, ticketek, tuentrada, venti
from app.scrapers.venues import canonical_venue

SCRAPERS: dict[str, Callable[[], list[Event]]] = {
    "colon": colon.scrape,
    "livepass": livepass.scrape,
    "venti": venti.scrape,
    "movistar": movistar.scrape,
    "ticketek": ticketek.scrape,
    "tuentrada": tuentrada.scrape,
    "allaccess": allaccess.scrape,
    "enigma": enigma.scrape,
    "coolco": coolco.scrape,
    "articket": articket.scrape,
    "pulso": pulso.scrape,
    "granrivadavia": granrivadavia.scrape,
}
PARTIAL_RATIO = 0.7  # fewer events than this share of what is stored raises a warning


class UnknownSourceError(ValueError):
    pass


def check_sources(only: list[str] | None, scrapers: Mapping[str, object]) -> None:
    unknown = [name for name in only or [] if name not in scrapers]
    if unknown:
        raise UnknownSourceError(f"Unknown source {', '.join(unknown)}; valid ones: {', '.join(scrapers)}")


@dataclass
class Report:
    counts: dict[str, int] = field(default_factory=dict)  # events scraped per source
    errors: dict[str, str] = field(default_factory=dict)  # source -> what went wrong
    warnings: dict[str, str] = field(default_factory=dict)  # source -> suspiciously few events
    saved: int = 0


# first_seen_at of the shows found on a source's first run: older than any "just announced" window.
SEEN_BEFORE_WATCHING = datetime(2000, 1, 1, tzinfo=timezone.utc)


def run(
    scrapers: dict[str, Callable[[], list[Event]]],
    enrich: Callable[[list[Event]], list[Event]],
    save: Callable[[list[Event]], None],
    only: list[str] | None = None,
    log: Callable[[str], None] = lambda _: None,
    known: dict[str, int] | None = None,
    new_sources: Collection[str] = (),
) -> Report:
    """`known` is how many upcoming events of each source are already stored: a source that now
    returns far fewer is flagged, because Movistar Arena has been seen loading only part of its listing.
    `new_sources` have nothing stored yet: what they list now is not news (see SEEN_BEFORE_WATCHING)."""
    check_sources(only, scrapers)
    report = Report()
    scraped: dict[str, Event] = {}
    for name, scrape in scrapers.items():
        if only and name not in only:
            continue
        log(f"[{name}] scraping...")
        try:
            found = scrape()
        except Exception as error:  # one broken site must not stop the rest
            report.errors[name] = f"{type(error).__name__}: {error}"
            log(f"[{name}] failed: {report.errors[name]}")
            continue
        report.counts[name] = len(found)
        log(f"[{name}] {len(found)} events")
        stored = (known or {}).get(name, 0)
        if stored and len(found) < stored * PARTIAL_RATIO:
            report.warnings[name] = (
                f"found {len(found)} events but {stored} upcoming ones are stored; "
                "the site may have loaded only part of its listing, run it again"
            )
            log(f"[{name}] WARNING: {report.warnings[name]}")
        found = [event.model_copy(update={"venue": canonical_venue(event.venue, event.city)}) for event in found]
        if name in new_sources:
            log(f"[{name}] first run: its shows are not counted as just announced")
            found = [event.model_copy(update={"first_seen_at": SEEN_BEFORE_WATCHING}) for event in found]
        scraped.update({event.id: event for event in found})  # same id twice: the last one wins
    if not scraped:
        return report
    log("choosing images...")
    events = enrich(list(scraped.values()))
    log(f"saving {len(events)} events...")
    save(events)
    report.saved = len(events)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.run", description=__doc__.split("\n")[0])
    parser.add_argument("--only", help=f"comma-separated sources to run ({', '.join(SCRAPERS)}); default: all")
    args = parser.parse_args(argv)
    only = [name.strip() for name in args.only.split(",") if name.strip()] if args.only else None

    try:
        check_sources(only, SCRAPERS)  # before opening the database
    except UnknownSourceError as error:
        print(error, file=sys.stderr)
        return 2
    engine = make_engine()  # also loads server/.env
    try:
        user_agent()  # fail now, not after minutes of scraping, if the Wikimedia contact is missing
    except MissingContactError as error:
        print(error, file=sys.stderr)
        return 2
    migrate(engine)
    with engine.connect() as connection:
        known = count_upcoming_by_source(connection, datetime.now(timezone.utc))
        new_sources = set(SCRAPERS) - stored_sources(connection)
    store = LocalImageStore(IMAGES_DIR)

    def save(events: list[Event]) -> None:
        with engine.begin() as connection:
            upsert_events(connection, events)

    try:
        report = run(SCRAPERS, lambda events: enrich_images(add_artists(events), store), save, only, log=print, known=known, new_sources=new_sources)
    finally:
        engine.dispose()
    print(f"\nsaved {report.saved} events; scraped per source: {report.counts or 'none'}")
    for name, problem in report.warnings.items():
        print(f"WARNING {name}: {problem}", file=sys.stderr)
    for name, problem in report.errors.items():
        print(f"FAILED {name}: {problem}", file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
