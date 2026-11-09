"""One command for the whole trip: scrape every source, choose each event's image, store them.

    python -m app.run                   # all sources
    python -m app.run --only colon,venti

A source that fails is reported and skipped; the others still run. Events already stored are
updated, not duplicated. Events that a site stops listing are not removed (yet).
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Callable

from app.db import SERVER_DIR, make_engine, migrate
from app.domain.event import Event
from app.events_repository import upsert_events
from app.images.copy import LocalImageStore
from app.images.wikimedia import MissingContactError, user_agent
from app.pipeline import enrich_images
from app.scrapers import colon, livepass, movistar, venti

SCRAPERS: dict[str, Callable[[], list[Event]]] = {
    "colon": colon.scrape,
    "livepass": livepass.scrape,
    "venti": venti.scrape,
    "movistar": movistar.scrape,
}
IMAGES_DIR = SERVER_DIR / "data" / "images"


@dataclass
class Report:
    counts: dict[str, int] = field(default_factory=dict)  # events scraped per source
    errors: dict[str, str] = field(default_factory=dict)  # source -> what went wrong
    saved: int = 0


def run(
    scrapers: dict[str, Callable[[], list[Event]]],
    enrich: Callable[[list[Event]], list[Event]],
    save: Callable[[list[Event]], None],
    only: list[str] | None = None,
    log: Callable[[str], None] = lambda _: None,
) -> Report:
    unknown = [name for name in only or [] if name not in scrapers]
    if unknown:
        raise ValueError(f"Unknown source {', '.join(unknown)}; valid ones: {', '.join(scrapers)}")
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

    engine = make_engine()  # also loads server/.env
    try:
        user_agent()  # fail now, not after minutes of scraping, if the Wikimedia contact is missing
    except MissingContactError as error:
        print(error, file=sys.stderr)
        return 2
    migrate(engine)
    store = LocalImageStore(IMAGES_DIR)

    def save(events: list[Event]) -> None:
        with engine.begin() as connection:
            upsert_events(connection, events)

    try:
        report = run(SCRAPERS, lambda events: enrich_images(events, store), save, only, log=print)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    finally:
        engine.dispose()
    print(f"\nsaved {report.saved} events; scraped per source: {report.counts or 'none'}")
    for name, problem in report.errors.items():
        print(f"FAILED {name}: {problem}", file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
