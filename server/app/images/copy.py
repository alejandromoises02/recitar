"""Copies of the images that some sources publish, stored by us and resized.

A copy is not a licence: the event keeps `image_origin="source"` and the original URL in
`image_source_url`, so the "replace before a public launch" check still finds it.
"""

import hashlib
import io
import time
from pathlib import Path
from typing import Callable

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from app.domain.event import Event

# Sources whose images we copy. Movistar Arena's terms forbid it, so it has its own plan.
COPY_SOURCES = ("colon", "livepass", "venti")
MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024
MAX_WIDTH = 800
MEDIA_PREFIX = "/media/"
# Where copies live and where the API serves them from (`/media/...`). Files are never rewritten:
# a name is the hash of the source URL and an image already stored is not downloaded again.
IMAGES_DIR = Path(__file__).resolve().parents[2] / "data" / "images"


class LocalImageStore:
    """Files on disk, named by a hash of the source URL. The API will serve them under /media/."""

    def __init__(self, root: Path, public_prefix: str = MEDIA_PREFIX) -> None:
        self.root = Path(root)
        self.public_prefix = public_prefix

    def _name(self, source_url: str) -> str:
        return hashlib.sha256(source_url.encode()).hexdigest()[:32] + ".webp"

    def url_for(self, source_url: str) -> str:
        return self.public_prefix + self._name(source_url)

    def has(self, source_url: str) -> bool:
        return (self.root / self._name(source_url)).exists()

    def save(self, source_url: str, webp: bytes) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / self._name(source_url)).write_bytes(webp)
        return self.url_for(source_url)

    def file_for(self, public_url: str) -> Path | None:
        """The file behind one of our public URLs, or None if the URL is not one of ours."""
        name = public_url.removeprefix(self.public_prefix)
        if not public_url.startswith(self.public_prefix) or not name or "/" in name or name.startswith("."):
            return None
        return self.root / name


def _to_webp(data: bytes) -> bytes | None:
    """Decode (which also proves it is an image), apply EXIF rotation, shrink to MAX_WIDTH, encode."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            if image.width > MAX_WIDTH:
                image = image.resize((MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)), Image.LANCZOS)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            out = io.BytesIO()
            image.save(out, "WEBP", quality=82)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return None


def _download(client: httpx.Client, url: str) -> bytes | None:
    try:
        response = client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code != 200 or len(response.content) > MAX_DOWNLOAD_BYTES:
        return None
    return response.content


def fetch_webp(client: httpx.Client, url: str) -> bytes | None:
    """Download an image and shrink it to WebP, or None if either step fails."""
    data = _download(client, url)
    return _to_webp(data) if data else None


def store_remote_image(client: httpx.Client, store: LocalImageStore, source_url: str) -> str | None:
    """Download one image, shrink it to WebP and store it. Returns our public URL, or None if it fails."""
    if store.has(source_url):
        return store.url_for(source_url)
    webp = fetch_webp(client, source_url)
    return store.save(source_url, webp) if webp else None


def copy_event_images(
    events: list[Event],
    client: httpx.Client,
    store: LocalImageStore,
    sources: tuple[str, ...] = COPY_SOURCES,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Event]:
    """Point each event of the chosen sources to our copy of its image. Anything that fails is
    left as the source published it. The same image (every date of a show) is downloaded once."""
    copied: dict[str, str | None] = {}
    result: list[Event] = []
    for event in events:
        source_url = event.image_url
        if not source_url or event.id.split("-", 1)[0] not in sources:
            result.append(event)
            continue
        if source_url not in copied:
            if store.has(source_url):
                copied[source_url] = store.url_for(source_url)
            else:
                sleep(delay)
                webp = _to_webp(data) if (data := _download(client, source_url)) else None
                copied[source_url] = store.save(source_url, webp) if webp else None
        local = copied[source_url]
        result.append(event.model_copy(update={"image_url": local, "image_source_url": source_url}) if local else event)
    return result
