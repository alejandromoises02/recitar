import io
from datetime import datetime, timezone

import httpx
from PIL import Image

from app.domain.event import Event, TicketLink
from app.images.copy import LocalImageStore
from app.pipeline import enrich_images
from tests.test_wikimedia import api

NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)
SOURCE_URL = "https://img.example.com/poster.png"


def source_images() -> httpx.Client:
    buffer = io.BytesIO()
    Image.new("RGB", (1000, 500), (200, 30, 30)).save(buffer, "PNG")
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=buffer.getvalue())))


def event(id_: str, title: str, **extra) -> Event:
    return Event(
        id=id_, category="concert", title=title, venue="V", starts_at=NOW,
        ticket_links=[TicketLink(vendor="X", url="https://x.com")], source_url="https://x.com/e",
        updated_at=NOW, **extra,
    )


def run(events, tmp_path):
    return enrich_images(
        events, LocalImageStore(tmp_path), source_client=source_images(), wikimedia_client=api(), delay=0,
        sleep=lambda _: None,
    )


def test_each_source_gets_the_image_policy_it_has(tmp_path):
    venti = event("venti-a-20261120T2100", "Some Show", image_url=SOURCE_URL, image_origin="source")
    movistar = event("movistar-b-20261121T2100", "Divididos")
    copied, licensed = run([venti, movistar], tmp_path)
    assert copied.image_origin == "source" and copied.image_url.startswith("/media/")
    assert copied.image_source_url == SOURCE_URL
    assert licensed.image_origin == "licensed" and licensed.image_license == "CC BY 3.0"


def test_a_movistar_title_that_is_not_an_artist_stays_without_image(tmp_path):
    (result,) = run([event("movistar-b-20261121T2100", "DISNEY")], tmp_path)
    assert result.image_url is None


def test_the_order_of_the_events_is_kept(tmp_path):
    events = [event("movistar-b-20261121T2100", "Divididos"), event("colon-a-20261120T2100", "Opera")]
    assert [e.id for e in run(events, tmp_path)] == [e.id for e in events]
