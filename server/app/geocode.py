"""Fill in where venues are from OpenStreetMap (Nominatim), for those no ticketer placed.

    python -m app.geocode

Run it after app.run. It asks only for venues without coordinates, one request per second (Nominatim's
usage policy), with the contact from SCRAPER_CONTACT_EMAIL in the User-Agent. A venue whose request
fails stays without coordinates and the others go on; it is asked again next time.

A result is accepted only inside the venue's own region and only when it is a place: as checked on
2026-11-18, "Club Ciudad, Buenos Aires" first returns clubs in Buenos Aires province and "Hipódromo de
Palermo" first returns two bus stops, so the first acceptable of five results is taken.
"""

import sys
import time
from dataclasses import dataclass, field
from typing import Callable

import httpx
from sqlalchemy import Connection

from app.db import make_engine, migrate
from app.events_repository import store_geocoded, venues_to_geocode
from app.images.wikimedia import MissingContactError, build_client

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Result categories that name a street, a stop or a whole town, never a venue.
NOT_A_PLACE = {"highway", "place", "boundary"}


@dataclass(frozen=True)
class Place:
    latitude: float
    longitude: float
    address: str | None  # street and number, when OpenStreetMap has them


@dataclass
class GeocodeReport:
    found: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)  # Nominatim has no acceptable place for them
    failed: dict[str, str] = field(default_factory=dict)  # venue -> what went wrong


def pick_place(results: list[dict], region: str) -> Place | None:
    for result in results:
        details = result.get("address") or {}
        if result.get("category") in NOT_A_PLACE or details.get("ISO3166-2-lvl4") != region:
            continue
        street = " ".join(part for part in (details.get("road"), details.get("house_number")) if part)
        return Place(float(result["lat"]), float(result["lon"]), street or None)
    return None


def geocode_venues(
    connection: Connection,
    client: httpx.Client,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = lambda _: None,
) -> GeocodeReport:
    report = GeocodeReport()
    for venue in venues_to_geocode(connection):
        query = ", ".join(part for part in (venue.name, venue.city, "Argentina") if part)
        try:
            response = client.get(NOMINATIM_URL, params={
                "q": query, "format": "jsonv2", "addressdetails": 1, "limit": 5, "countrycodes": "ar",
            })
            response.raise_for_status()
            place = pick_place(response.json(), venue.region)
        except (httpx.HTTPError, ValueError, KeyError) as error:  # one bad answer must not stop the rest
            report.failed[venue.name] = f"{type(error).__name__}: {error}"
            log(f"[{venue.name}] failed: {report.failed[venue.name]}")
        else:
            if place is None:
                report.missed.append(venue.name)
                log(f"[{venue.name}] not found")
            else:
                store_geocoded(connection, venue.name, place.latitude, place.longitude, place.address)
                report.found.append(venue.name)
                log(f"[{venue.name}] {place.latitude}, {place.longitude}")
        sleep(delay)
    return report


def main() -> int:
    engine = make_engine()  # also loads server/.env
    try:
        client = build_client()
    except MissingContactError as error:
        print(error, file=sys.stderr)
        return 2
    migrate(engine)
    try:
        with client, engine.begin() as connection:
            report = geocode_venues(connection, client, log=print)
    finally:
        engine.dispose()
    print(f"\nplaced {len(report.found)} venues; not found: {len(report.missed)}; failed: {len(report.failed)}")
    for name, problem in report.failed.items():
        print(f"FAILED {name}: {problem}", file=sys.stderr)
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
