"""Rebuild the image copies from the database on a host whose disk starts empty.

    python -m app.images.restore

The copies live in server/data/images, which git ignores, so a fresh host (the free demo deploy
builds from the repository) has none and every /media/ link would break. Each stored event that
points to a copy keeps the original URL in image_source_url, and a copy's file name is the hash of
that URL, so downloading the original again puts the copy back at the same path. Run it as part of
the build: files written then are kept, while files written by the running service are not.
"""

import sys
import time
from collections.abc import Callable, Iterable

import httpx
from sqlalchemy import select

from app.db import make_engine
from app.events_repository import events
from app.images.copy import IMAGES_DIR, MEDIA_PREFIX, LocalImageStore, store_remote_image
from app.pipeline import SOURCE_USER_AGENT

DELAY = 0.5  # between downloads, to stay polite with the sources


def copied_sources(rows: Iterable[tuple[str | None, str | None]], store: LocalImageStore) -> list[str]:
    """The original URLs behind (image_url, image_source_url) rows that point to our copy of them,
    once each, in order."""
    found: dict[str, None] = {}
    for image_url, source_url in rows:
        if image_url and source_url and image_url.startswith(MEDIA_PREFIX) and image_url == store.url_for(source_url):
            found.setdefault(source_url)
    return list(found)


def restore(
    source_urls: list[str],
    client: httpx.Client,
    store: LocalImageStore,
    delay: float = DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, int]:
    """Put back each copy that is missing. Returns (copies present afterwards, copies that failed)."""
    restored = failed = 0
    for source_url in source_urls:
        if not store.has(source_url):
            sleep(delay)
        if store_remote_image(client, store, source_url):
            restored += 1
        else:
            failed += 1
    return restored, failed


def main() -> int:
    store = LocalImageStore(IMAGES_DIR)
    with make_engine().connect() as connection:
        rows = connection.execute(select(events.c.image_url, events.c.image_source_url)).all()
    sources = copied_sources(rows, store)
    with httpx.Client(headers={"User-Agent": SOURCE_USER_AGENT}, timeout=20) as client:
        restored, failed = restore(sources, client, store)
    print(f"image copies: {restored} present, {failed} failed (of {len(sources)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
