"""The step after scraping: decide which image each event ends up with.

Colón, Livepass and Venti publish an image we copy. Movistar Arena's terms forbid using its
images, so its events get a free, credited photo of the artist from Wikimedia Commons, looked up
by the event title. Anything that cannot be resolved stays without an image.
"""

import time
from typing import Callable

import httpx

from app.domain.event import Event
from app.domain.titles import tidy_title
from app.images.copy import LocalImageStore, copy_event_images
from app.images.wikimedia import add_wikimedia_images, build_client

SOURCE_USER_AGENT = "recitAR-research/0.1"


def enrich_images(
    events: list[Event],
    store: LocalImageStore,
    source_client: httpx.Client | None = None,
    wikimedia_client: httpx.Client | None = None,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Event]:
    """Without clients, real ones are built; the Wikimedia one needs SCRAPER_CONTACT_EMAIL."""
    own_source = source_client is None
    own_wikimedia = wikimedia_client is None
    source_client = source_client or httpx.Client(headers={"User-Agent": SOURCE_USER_AGENT}, timeout=20)
    wikimedia_client = wikimedia_client or build_client()
    try:
        copied = copy_event_images(events, source_client, store, delay=delay, sleep=sleep)
        return add_wikimedia_images(copied, wikimedia_client, store, delay=delay, sleep=sleep)
    finally:
        if own_source:
            source_client.close()
        if own_wikimedia:
            wikimedia_client.close()


def add_artists(events: list[Event]) -> list[Event]:
    """Fills an empty artist from the title (domain/titles.py); one the source gave is kept. Stored,
    so search and the image lookup can use it."""
    return [
        event if event.artist is not None
        else event.model_copy(update={"artist": tidy_title(event.title, event.id.split("-", 1)[0], event.venue, event.city).artist})
        for event in events
    ]
