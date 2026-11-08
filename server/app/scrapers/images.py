"""Image URLs as the sources publish them. Nothing is downloaded here."""

from typing import Any


def first_image_url(value: Any) -> str | None:
    """schema.org `image` can be a URL, a list of them or an ImageObject; keep the first absolute URL."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        value = value.get("url")
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    return None


def source_image(url: str | None) -> dict[str, str]:
    """Event fields for an image taken from the ticket seller itself (unlicensed, see ImageOrigin)."""
    return {"image_url": url, "image_origin": "source"} if url else {}
