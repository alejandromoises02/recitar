"""Rebuilding the image copies on a host whose disk starts empty (the free demo host): each stored
event that points to one of our copies names the original in image_source_url, and a copy's file
name is the hash of that URL, so downloading it again lands it at the same /media/ path."""

import io
from pathlib import Path

import httpx
from PIL import Image

from app.images.copy import LocalImageStore
from app.images.restore import copied_sources, restore

POSTER = "https://img.example.com/poster.png"
BANNER = "https://img.example.com/banner.png"


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 600), (20, 120, 40)).save(buffer, "PNG")
    return buffer.getvalue()


def test_only_rows_that_point_to_our_copy_of_their_source_are_restored(tmp_path: Path):
    store = LocalImageStore(tmp_path)
    rows = [
        (store.url_for(POSTER), POSTER),
        (store.url_for(POSTER), POSTER),  # every date of a show: one download
        (store.url_for(BANNER), BANNER),
        ("https://other.example.com/x.jpg", None),  # an image we never copied
        ("/media/somethingelse.webp", POSTER),  # does not match the source's name: not ours to rebuild
        (None, None),
    ]
    assert copied_sources(rows, store) == [POSTER, BANNER]


def test_restore_downloads_each_missing_copy_to_its_stored_path_and_counts_failures(tmp_path: Path):
    store = LocalImageStore(tmp_path)
    requested: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(200, content=png()) if str(request.url) == POSTER else httpx.Response(404)

    sleeps: list[float] = []
    with httpx.Client(transport=httpx.MockTransport(answer)) as client:
        restored, failed = restore([POSTER, BANNER], client, store, delay=0.5, sleep=sleeps.append)

    assert (restored, failed) == (1, 1)
    assert (tmp_path / store.url_for(POSTER).removeprefix("/media/")).exists()
    assert not store.has(BANNER)
    assert requested == [POSTER, BANNER]
    assert sleeps == [0.5, 0.5]


def test_a_copy_already_on_disk_is_not_downloaded_again(tmp_path: Path):
    store = LocalImageStore(tmp_path)
    store.save(POSTER, b"already here")

    def answer(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected download of {request.url}")

    with httpx.Client(transport=httpx.MockTransport(answer)) as client:
        assert restore([POSTER], client, store, delay=0, sleep=lambda _s: None) == (1, 0)
