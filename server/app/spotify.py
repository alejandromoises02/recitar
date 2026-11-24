"""Find each artist's Spotify id, so a show page can embed a sample of their music.

    python -m app.spotify

Run it after app.run. It asks only for artists of upcoming shows never looked up, plus those Spotify
did not have a month ago (an act may have joined since). It uses the app credentials from
SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (Client Credentials flow: no user logs in, and the secret
stays on the server). An artist whose request fails is asked again next time; the others go on.

Checked on 2026-11-24: search answers at most 10 artists per request (limit=11 is a 400), gives no
popularity or follower counts in development mode, and returns ten loosely related artists even for
a made-up name. So an artist is accepted only when its name matches ours exactly (case, accents and
spaces aside), and the first such one, as Spotify ranks them, is taken.
"""

import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

import httpx
from dotenv import load_dotenv
from sqlalchemy import Connection

from app.db import SERVER_DIR, make_engine, migrate
from app.domain.titles import fold
from app.events_repository import artists_to_look_up, store_spotify_artist

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
SEARCH_LIMIT = 10  # the most Spotify allows for an app in development mode
RECHECK_AFTER = timedelta(days=30)


class MissingSpotifyCredentialsError(RuntimeError):
    pass


@dataclass
class SpotifyReport:
    found: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)  # Spotify has no artist of that name
    failed: dict[str, str] = field(default_factory=dict)  # artist -> what went wrong


def spotify_credentials() -> tuple[str, str]:
    load_dotenv(SERVER_DIR / ".env")
    values = {name: (os.environ.get(name) or "").strip() for name in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET")}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise MissingSpotifyCredentialsError(f"Set {' and '.join(missing)} in server/.env (see server/README.md)")
    return values["SPOTIFY_CLIENT_ID"], values["SPOTIFY_CLIENT_SECRET"]


def _key(name: str) -> str:
    return " ".join(fold(name).split())


def pick_artist(items: list[dict], name: str) -> str | None:
    wanted = _key(name)
    return next((item["id"] for item in items if _key(item.get("name") or "") == wanted), None)


def _token(client: httpx.Client, credentials: tuple[str, str]) -> str:
    response = client.post(TOKEN_URL, data={"grant_type": "client_credentials"}, auth=credentials)
    response.raise_for_status()
    return response.json()["access_token"]


def look_up_artists(
    connection: Connection,
    client: httpx.Client,
    credentials: tuple[str, str],
    now: datetime,
    delay: float = 0.2,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = lambda _: None,
) -> SpotifyReport:
    """A rejected token raises before any search: nothing else would work either."""
    report = SpotifyReport()
    names = artists_to_look_up(connection, now, RECHECK_AFTER)
    if not names:
        return report
    headers = {"Authorization": f"Bearer {_token(client, credentials)}"}
    for name in names:
        try:
            response = client.get(SEARCH_URL, params={"q": name, "type": "artist", "limit": SEARCH_LIMIT}, headers=headers)
            response.raise_for_status()
            spotify_id = pick_artist(response.json()["artists"]["items"], name)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:  # one bad answer must not stop the rest
            report.failed[name] = f"{type(error).__name__}: {error}"
            log(f"[{name}] failed: {report.failed[name]}")
        else:
            store_spotify_artist(connection, name, spotify_id, now)
            (report.found if spotify_id else report.missed).append(name)
            log(f"[{name}] {spotify_id or 'not found'}")
        sleep(delay)
    return report


def main() -> int:
    engine = make_engine()  # also loads server/.env
    try:
        credentials = spotify_credentials()
    except MissingSpotifyCredentialsError as error:
        print(error, file=sys.stderr)
        return 2
    migrate(engine)
    try:
        with httpx.Client(timeout=20) as client, engine.begin() as connection:
            report = look_up_artists(connection, client, credentials, datetime.now(timezone.utc), log=print)
    finally:
        engine.dispose()
    print(f"\nfound {len(report.found)} artists; not on Spotify: {len(report.missed)}; failed: {len(report.failed)}")
    for name, problem in report.failed.items():
        print(f"FAILED {name}: {problem}", file=sys.stderr)
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
