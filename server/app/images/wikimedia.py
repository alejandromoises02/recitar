"""Free photos of artists from Wikidata and Wikimedia Commons.

Wikidata links an artist to a Commons file (property P18); Commons publishes its author and
licence. Only licences that allow commercial reuse with credit are accepted. The copy we store
keeps the credit, the licence and the Commons page, so the client can show them.
"""

import json
import os
import re
import time
import unicodedata
from typing import Any, Callable, Mapping
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.domain.event import Event
from app.images.copy import LocalImageStore, store_remote_image

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_PAGE_PREFIX = "https://commons.wikimedia.org/wiki/"
COMMONS_FILE_PAGE = COMMONS_PAGE_PREFIX + "File:"
CONTACT_VARIABLE = "SCRAPER_CONTACT_EMAIL"
USER_AGENT_NAME = "recitAR-research/0.1"
THUMB_WIDTH = 800
# Sources whose events get a free artist photo (they do not publish an image we may use).
WIKIMEDIA_SOURCES = ("movistar",)

# Commercial reuse with credit: CC0, public domain, CC BY and CC BY-SA. NC, ND and GFDL are out.
_FREE_LICENSE = re.compile(r"CC0( 1\.0)?|Public domain|CC BY(-SA)? \d\.\d( [A-Za-z]{2,3})?", re.IGNORECASE)
_NO_CREDIT_NEEDED = re.compile(r"CC0.*|Public domain", re.IGNORECASE)
# The search result says what the entity is ("Argentine rock band"); albums and songs also match the name.
_PERFORMER = re.compile(
    r"band|singer|musician|rapper|group|duo|trio|DJ\b|composer|songwriter|guitarist|pianist|drummer"
    r"|banda|cantante|músic|rapero|grupo|dúo|compositor|guitarrista|pianista|baterista",
    re.IGNORECASE,
)
_RECORDING = re.compile(r"album|álbum|song|canción|single|EP\b|film|película", re.IGNORECASE)
_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp")


class MissingContactError(RuntimeError):
    """Wikimedia blocks bots without a contact in the User-Agent, and we never invent one."""


class LicensedImage(BaseModel):
    file_url: str  # a thumbnail on Wikimedia's servers
    author: str | None
    license: str
    page_url: str  # the Commons page where the image and its licence are published


def user_agent(env: Mapping[str, str] | None = None) -> str:
    contact = ((os.environ if env is None else env).get(CONTACT_VARIABLE) or "").strip()
    if not contact:
        raise MissingContactError(f"Set {CONTACT_VARIABLE} to the recitAR contact address (see server/README.md)")
    return f"{USER_AGENT_NAME} (contacto: {contact})"


def build_client(env: Mapping[str, str] | None = None) -> httpx.Client:
    return httpx.Client(headers={"User-Agent": user_agent(env)}, timeout=20, follow_redirects=True)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold().strip()


def _get_json(client: httpx.Client, url: str, params: dict[str, str], delay: float, sleep: Callable[[float], None]) -> Any:
    sleep(delay)
    try:
        response = client.get(url, params={**params, "format": "json"})
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except json.JSONDecodeError:  # e.g. an HTML error page served with 200
        return None


def _entity_id(name: str, search: Any) -> str | None:
    """First result named exactly like the artist and described as a performer, never a recording."""
    for result in (search or {}).get("search", []):
        description = result.get("description") or ""
        if _normalize(result.get("label") or "") != _normalize(name):
            continue
        if _PERFORMER.search(description) and not _RECORDING.search(description):
            return result["id"]
    return None


def _commons_file(claims: Any) -> str | None:
    statements = [s for s in ((claims or {}).get("claims", {}).get("P18") or []) if s.get("rank") != "deprecated"]
    statements.sort(key=lambda s: s.get("rank") != "preferred")
    for statement in statements:
        value = (statement.get("mainsnak") or {}).get("datavalue", {}).get("value")
        if isinstance(value, str) and value:
            return value
    return None


def _licensed_image(info: Any) -> LicensedImage | None:
    for page in ((info or {}).get("query", {}).get("pages") or {}).values():
        for item in page.get("imageinfo") or []:
            meta = item.get("extmetadata") or {}
            license_name = (meta.get("LicenseShortName") or {}).get("value", "").strip()
            thumb = item.get("thumburl")
            if not (_FREE_LICENSE.fullmatch(license_name) and thumb and item.get("mime") in _IMAGE_TYPES):
                continue
            author_html = (meta.get("Artist") or {}).get("value", "")
            author = BeautifulSoup(author_html, "html.parser").get_text(" ", strip=True) or None
            if author is None and not _NO_CREDIT_NEEDED.fullmatch(license_name):
                continue  # the licence requires credit and nobody is named
            return LicensedImage(file_url=thumb, author=author, license=license_name, page_url=item["descriptionurl"])
    return None


def find_artist_image(
    name: str,
    client: httpx.Client,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> LicensedImage | None:
    """Wikidata search -> the artist's P18 file -> its licence and author on Commons."""
    search = _get_json(
        client, WIKIDATA_API,
        {"action": "wbsearchentities", "search": name, "language": "es", "uselang": "es", "type": "item", "limit": "10"},
        delay, sleep,
    )
    entity = _entity_id(name, search)
    if entity is None:
        return None
    claims = _get_json(client, WIKIDATA_API, {"action": "wbgetclaims", "entity": entity, "property": "P18"}, delay, sleep)
    filename = _commons_file(claims)
    if filename is None:
        return None
    return _commons_image(f"File:{filename}", client, delay, sleep)


def _commons_image(title: str, client: httpx.Client, delay: float, sleep: Callable[[float], None]) -> LicensedImage | None:
    """A Commons file's thumbnail, author and licence, if its licence is free."""
    info = _get_json(
        client, COMMONS_API,
        {
            "action": "query", "titles": title, "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(THUMB_WIDTH),
        },
        delay, sleep,
    )
    return _licensed_image(info)


def commons_thumb_url(
    page_url: str,
    client: httpx.Client,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> str | None:
    """The current thumbnail of the Commons file whose page we stored (image_source_url), if it is
    still under a free licence. Anything that is not a Commons file page gives None, unasked."""
    if not page_url.startswith(COMMONS_FILE_PAGE):
        return None
    image = _commons_image(unquote(page_url.removeprefix(COMMONS_PAGE_PREFIX)), client, delay, sleep)
    return image.file_url if image else None


def add_wikimedia_images(
    events: list[Event],
    client: httpx.Client,
    store: LocalImageStore,
    sources: tuple[str, ...] = WIKIMEDIA_SOURCES,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Event]:
    """Give a free, credited photo to the events of `sources` that have no image. The artist (or,
    until it is extracted, the title) is looked up once for all the dates of a show; whatever
    cannot be resolved stays without an image."""
    found: dict[str, tuple[LicensedImage, str] | None] = {}
    result: list[Event] = []
    for event in events:
        name = (event.artist or event.title).strip()
        if event.image_url or event.id.split("-", 1)[0] not in sources or not name:
            result.append(event)
            continue
        if name not in found:
            image = find_artist_image(name, client, delay, sleep)
            if image is not None:
                sleep(delay)
            local = store_remote_image(client, store, image.file_url) if image else None
            found[name] = (image, local) if image and local else None
        match = found[name]
        if match is None:
            result.append(event)
            continue
        image, local = match
        result.append(event.model_copy(update={
            "image_url": local, "image_origin": "licensed", "image_author": image.author,
            "image_license": image.license, "image_source_url": image.page_url,
        }))
    return result
