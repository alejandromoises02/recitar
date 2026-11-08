import io
from datetime import datetime, timezone
from pathlib import Path

import httpx
from PIL import Image

from app.domain.event import Event, TicketLink
from app.images.copy import COPY_SOURCES, LocalImageStore, copy_event_images

NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)
URL = "https://img.example.com/poster.png"


def png(size=(1600, 900)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def event(id_: str = "venti-a-20261120T2100", image_url: str | None = URL, **extra) -> Event:
    return Event(
        id=id_, category="concert", title="Show", venue="V", starts_at=NOW,
        ticket_links=[TicketLink(vendor="X", url="https://x.com")], source_url="https://x.com/e",
        image_url=image_url, image_origin="source" if image_url else None, updated_at=NOW, **extra,
    )


def run(events, handler, tmp_path: Path, **kwargs):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    store = LocalImageStore(tmp_path)
    return copy_event_images(events, client, store, delay=0, sleep=lambda _: None, **kwargs), store


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=png(), headers={"content-type": "image/png"})


def test_image_is_downloaded_resized_and_stored(tmp_path):
    (copied,), _ = run([event()], ok, tmp_path)
    files = list(tmp_path.glob("*.webp"))
    assert len(files) == 1
    with Image.open(files[0]) as saved:
        assert saved.width == 800 and saved.height == 450  # scaled down, ratio kept
    assert copied.image_url == f"/media/{files[0].name}"


def test_the_copy_is_still_marked_as_unlicensed_and_remembers_the_original(tmp_path):
    (copied,), _ = run([event()], ok, tmp_path)
    assert copied.image_origin == "source"
    assert copied.image_source_url == URL


def test_small_images_are_not_enlarged(tmp_path):
    handler = lambda r: httpx.Response(200, content=png((300, 200)), headers={"content-type": "image/png"})
    run([event()], handler, tmp_path)
    with Image.open(next(tmp_path.glob("*.webp"))) as saved:
        assert saved.width == 300


def test_same_image_for_many_dates_is_downloaded_once(tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url)
        return ok(request)

    events = [event("venti-a-20261120T2100"), event("venti-a-20261121T2100"), event("venti-a-20261122T2100")]
    copied, _ = run(events, handler, tmp_path)
    assert len(calls) == 1
    assert len({e.image_url for e in copied}) == 1


def test_an_existing_copy_is_reused_across_runs(tmp_path):
    run([event()], ok, tmp_path)
    calls = []
    run([event()], lambda r: calls.append(r) or ok(r), tmp_path)
    assert calls == []


def test_something_that_is_not_an_image_is_ignored(tmp_path):
    handler = lambda r: httpx.Response(200, content=b"<html>nope</html>", headers={"content-type": "image/png"})
    (kept,), _ = run([event()], handler, tmp_path)
    assert list(tmp_path.iterdir()) == []
    assert kept.image_url == URL  # left as the source published it


def test_a_failed_download_leaves_the_event_untouched(tmp_path):
    (kept,), _ = run([event()], lambda r: httpx.Response(404), tmp_path)
    assert kept == event()


def test_oversized_downloads_are_ignored(tmp_path):
    big = b"0" * (9 * 1024 * 1024)
    (kept,), _ = run([event()], lambda r: httpx.Response(200, content=big, headers={"content-type": "image/png"}), tmp_path)
    assert kept.image_url == URL and list(tmp_path.iterdir()) == []


def test_only_the_chosen_sources_are_copied(tmp_path):
    calls = []
    movistar = event("movistar-a-20261120T2100")
    (kept,), _ = run([movistar], lambda r: calls.append(r) or ok(r), tmp_path)
    assert calls == [] and kept == movistar
    assert set(COPY_SOURCES) == {"colon", "livepass", "venti"}


def test_events_without_an_image_are_left_alone(tmp_path):
    (kept,), _ = run([event(image_url=None)], ok, tmp_path)
    assert kept.image_url is None
