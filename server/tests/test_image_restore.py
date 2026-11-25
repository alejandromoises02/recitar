"""Rebuilding the image copies on a host whose disk starts empty (the free demo host): each stored
event that points to one of our copies names the original in image_source_url, and a copy's file
name is the hash of that URL, so downloading it again lands it at the same /media/ path."""

import io
from pathlib import Path

import httpx
from PIL import Image

from app.images.copy import LocalImageStore
from app.images.restore import copied_sources, licensed_targets, restore, restore_licensed

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


PAGE = "https://commons.wikimedia.org/wiki/File:Band.jpg"
THUMB = "https://thumb.wikimedia.org/band-800px.jpg?utm_content=thumbnail"


def test_licensed_rows_are_rebuilt_from_their_commons_page_once_per_stored_file():
    rows = [
        ("/media/aaaa.webp", PAGE, "licensed"),
        ("/media/aaaa.webp", PAGE, "licensed"),  # every date of a show
        ("/media/bbbb.webp", POSTER, "source"),  # a copy of the source: restore() handles it
        ("/media/cccc.webp", "https://example.com/not-commons", "licensed"),
        (None, PAGE, "licensed"),
    ]
    assert licensed_targets(rows) == [(PAGE, "/media/aaaa.webp")]


def test_a_licensed_copy_is_saved_under_the_name_already_stored_whatever_its_url_hashes_to(tmp_path: Path):
    store = LocalImageStore(tmp_path)
    resolved: list[str] = []

    def resolve(page: str) -> str | None:
        resolved.append(page)
        return THUMB if page == PAGE else None

    def answer(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=png()) if str(request.url) == THUMB else httpx.Response(404)

    missing = "https://commons.wikimedia.org/wiki/File:Gone.jpg"
    with httpx.Client(transport=httpx.MockTransport(answer)) as client:
        counts = restore_licensed(
            [(PAGE, "/media/aaaa.webp"), (missing, "/media/dddd.webp")], client, store, resolve, delay=0, sleep=lambda _s: None,
        )
    assert counts == (1, 1)
    assert (tmp_path / "aaaa.webp").read_bytes()[:4] == b"RIFF"  # WebP
    assert not (tmp_path / "dddd.webp").exists()
    assert resolved == [PAGE, missing]


def test_a_licensed_copy_already_on_disk_is_not_looked_up_again(tmp_path: Path):
    (tmp_path / "aaaa.webp").write_bytes(b"already here")

    def resolve(page: str) -> str | None:
        raise AssertionError("unexpected lookup")

    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404))) as client:
        assert restore_licensed([(PAGE, "/media/aaaa.webp")], client, LocalImageStore(tmp_path), resolve, delay=0) == (1, 0)


def test_only_a_plain_file_name_under_our_prefix_maps_to_a_file(tmp_path: Path):
    store = LocalImageStore(tmp_path)
    assert store.file_for("/media/aaaa.webp") == tmp_path / "aaaa.webp"
    for not_ours in ("/media/../secret.webp", "/media/sub/a.webp", "/media/", "/media/.hidden", "https://x.com/a.webp"):
        assert store.file_for(not_ours) is None
