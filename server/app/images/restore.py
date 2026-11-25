"""Rebuild the image copies from the database on a host whose disk starts empty.

    python -m app.images.restore

The copies live in server/data/images, which git ignores, so a fresh host (the free demo deploy
builds from the repository) has none and every /media/ link would break. A copy of a source's image
keeps the original URL in image_source_url and is named after its hash, so downloading the original
again puts it back at the same path. A licensed photo keeps its Commons page instead: its current
thumbnail is looked up there and saved under the name already stored. Wikimedia asks for a contact
(SCRAPER_CONTACT_EMAIL); without it the licensed photos are skipped, not the build. Run it as part of
the build: files written then are kept, while files written by the running service are not.
"""

import sys
import time
from collections.abc import Callable, Iterable

import httpx
from sqlalchemy import select

from app.db import make_engine
from app.events_repository import events
from app.images.copy import IMAGES_DIR, MEDIA_PREFIX, LocalImageStore, fetch_webp, store_remote_image
from app.images.wikimedia import COMMONS_FILE_PAGE, MissingContactError, build_client, commons_thumb_url
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


def licensed_targets(rows: Iterable[tuple[str | None, str | None, str | None]]) -> list[tuple[str, str]]:
    """(Commons page, stored /media/ URL) of each licensed photo, once per stored file. A licensed
    copy is named after the thumbnail URL, which we do not store (it carries tracking parameters that
    change), so it is rebuilt from its Commons page and saved under the name already stored."""
    found: dict[str, str] = {}
    for image_url, page_url, origin in rows:
        if origin == "licensed" and image_url and image_url.startswith(MEDIA_PREFIX) and page_url \
                and page_url.startswith(COMMONS_FILE_PAGE):
            found.setdefault(image_url, page_url)
    return [(page, image_url) for image_url, page in found.items()]


def restore_licensed(
    targets: list[tuple[str, str]],
    client: httpx.Client,
    store: LocalImageStore,
    resolve: Callable[[str], str | None],
    delay: float = DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, int]:
    """Put back each missing licensed photo: find its current thumbnail with `resolve`, download it
    and save it at the stored path. Returns (photos present afterwards, photos that failed)."""
    restored = failed = 0
    for page_url, image_url in targets:
        path = store.file_for(image_url)
        if path is None:
            failed += 1
            continue
        if path.exists():
            restored += 1
            continue
        thumb = resolve(page_url)
        sleep(delay)
        webp = fetch_webp(client, thumb) if thumb else None
        if webp is None:
            failed += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(webp)
        restored += 1
    return restored, failed


def main() -> int:
    store = LocalImageStore(IMAGES_DIR)
    columns = (events.c.image_url, events.c.image_source_url, events.c.image_origin)
    with make_engine().connect() as connection:
        rows = connection.execute(select(*columns)).all()
    sources = copied_sources(((url, source) for url, source, _ in rows), store)
    with httpx.Client(headers={"User-Agent": SOURCE_USER_AGENT}, timeout=20) as client:
        restored, failed = restore(sources, client, store)
    print(f"image copies: {restored} present, {failed} failed (of {len(sources)})")
    targets = licensed_targets(rows)
    try:
        wikimedia = build_client()
    except MissingContactError:
        print(f"licensed photos: skipped {len(targets)}, set SCRAPER_CONTACT_EMAIL (Wikimedia asks for a contact)")
        return 0
    with wikimedia:
        restored, failed = restore_licensed(targets, wikimedia, store, lambda page: commons_thumb_url(page, wikimedia))
    print(f"licensed photos: {restored} present, {failed} failed (of {len(targets)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
