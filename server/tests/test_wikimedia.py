import io
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.domain.event import Event, TicketLink
from app.images.copy import LocalImageStore
from app.images.wikimedia import (
    MissingContactError,
    add_wikimedia_images,
    find_artist_image,
    user_agent,
)

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 8, tzinfo=timezone.utc)
THUMB_PREFIX = "https://thumb.wikimedia.org/"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (960, 720), (20, 40, 200)).save(buffer, "PNG")
    return buffer.getvalue()


def api(search=None, claims=None, info=None, requests: list | None = None):
    """A fake Wikimedia: Wikidata search, Wikidata claims, Commons image info, image bytes."""
    search = fixture("wikidata_search_divididos.json") if search is None else search
    claims = fixture("wikidata_p18_divididos.json") if claims is None else claims
    info = fixture("commons_imageinfo_divididos.json") if info is None else info

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        if request.url.host == "thumb.wikimedia.org":
            return httpx.Response(200, content=png())
        action = request.url.params.get("action")
        if action == "wbsearchentities":
            return httpx.Response(200, json=search)
        if action == "wbgetclaims":
            return httpx.Response(200, json=claims)
        if action == "query":
            return httpx.Response(200, json=info)
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def with_license(short_name: str) -> dict:
    info = fixture("commons_imageinfo_divididos.json")
    page = next(iter(info["query"]["pages"].values()))
    page["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"] = short_name
    return info


def lookup(name: str, client: httpx.Client):
    return find_artist_image(name, client, delay=0, sleep=lambda _: None)


def test_the_user_agent_carries_the_contact_from_the_environment():
    agent = user_agent({"SCRAPER_CONTACT_EMAIL": "bot@example.com"})
    assert agent == "recitAR-research/0.1 (contacto: bot@example.com)"


def test_without_a_contact_there_is_no_user_agent():
    with pytest.raises(MissingContactError):
        user_agent({})
    with pytest.raises(MissingContactError):
        user_agent({"SCRAPER_CONTACT_EMAIL": "  "})


def test_a_band_is_resolved_to_its_commons_photo_with_credit_and_licence():
    image = lookup("Divididos", api())
    assert image is not None
    assert image.file_url.startswith(THUMB_PREFIX) and "&utm_campaign=imageinfo" in image.file_url
    assert image.author == "Elemaki"  # the HTML link around the name is stripped
    assert image.license == "CC BY 3.0"
    assert image.page_url == "https://commons.wikimedia.org/wiki/File:Divididos.JPG"


def test_the_name_match_ignores_case_and_accents():
    assert lookup("DIVIDIDOS", api()) is not None


def test_albums_and_fuzzy_matches_are_not_the_artist():
    # Same search results, but the band is not among them: the album called exactly "Divididos" and
    # "Divididos por la felicidad" must not be taken for it.
    search = fixture("wikidata_search_divididos.json")
    search["search"] = search["search"][1:]
    assert lookup("Divididos", api(search=search)) is None


def test_an_artist_without_a_wikidata_photo_gives_nothing():
    assert lookup("Divididos", api(claims={"claims": {}})) is None


def test_a_name_nobody_matches_gives_nothing():
    assert lookup("Nobody At All", api()) is None


@pytest.mark.parametrize("short_name", ["CC BY 3.0", "CC BY-SA 4.0", "CC BY 2.0 de", "CC0", "Public domain"])
def test_free_licences_are_accepted(short_name):
    assert lookup("Divididos", api(info=with_license(short_name))) is not None


@pytest.mark.parametrize("short_name", ["CC BY-NC 2.0", "CC BY-ND 4.0", "CC BY-NC-SA 3.0", "GFDL", "Fair use", ""])
def test_licences_that_do_not_allow_commercial_reuse_or_are_unknown_are_rejected(short_name):
    assert lookup("Divididos", api(info=with_license(short_name))) is None


def test_every_request_waits_the_delay_first():
    slept: list[float] = []
    find_artist_image("Divididos", api(), delay=1.5, sleep=slept.append)
    assert slept == [1.5, 1.5, 1.5]  # search, claims, image info


def test_a_server_error_means_no_photo_not_a_crash():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    assert lookup("Divididos", client) is None


def event(id_: str = "movistar-abc-20261120T2100", title: str = "Divididos", **extra) -> Event:
    return Event(
        id=id_, category="concert", title=title, venue="Movistar Arena", starts_at=NOW,
        ticket_links=[TicketLink(vendor="X", url="https://x.com")], source_url="https://x.com/e",
        updated_at=NOW, **extra,
    )


def enrich(events, client, tmp_path, **kwargs):
    store = LocalImageStore(tmp_path)
    result = add_wikimedia_images(events, client, store, delay=0, sleep=lambda _: None, **kwargs)
    return result, store


def test_a_movistar_event_gets_a_licensed_copy_with_credit(tmp_path):
    (result,), store = enrich([event()], api(), tmp_path)
    assert result.image_origin == "licensed"
    assert result.image_url == store.url_for(fixture("commons_imageinfo_divididos.json")["query"]["pages"]["3151685"]["imageinfo"][0]["thumburl"])
    assert result.image_author == "Elemaki"
    assert result.image_license == "CC BY 3.0"
    assert result.image_source_url == "https://commons.wikimedia.org/wiki/File:Divididos.JPG"
    assert Image.open(tmp_path / result.image_url.removeprefix("/media/")).format == "WEBP"


def test_the_artist_is_preferred_over_the_title(tmp_path):
    requests: list[httpx.Request] = []
    enrich([event(title="Divididos - Gira 2026", artist="Divididos")], api(requests=requests), tmp_path)
    assert requests[0].url.params["search"] == "Divididos"


def test_events_that_already_have_an_image_are_left_alone(tmp_path):
    kept = event(image_url="https://img.example.com/p.png", image_origin="source")
    (result,), _ = enrich([kept], api(), tmp_path)
    assert result == kept


def test_other_sources_are_left_alone(tmp_path):
    other = event(id_="venti-abc-20261120T2100")
    (result,), _ = enrich([other], api(), tmp_path)
    assert result == other


def test_an_unresolvable_event_stays_without_image(tmp_path):
    (result,), _ = enrich([event(title="Nobody At All")], api(), tmp_path)
    assert result.image_url is None and result.image_origin is None


def test_every_date_of_one_show_is_looked_up_once(tmp_path):
    requests: list[httpx.Request] = []
    events = [event("movistar-abc-20261120T2100"), event("movistar-abc-20261121T2100")]
    result, _ = enrich(events, api(requests=requests), tmp_path)
    assert [e.image_origin for e in result] == ["licensed", "licensed"]
    assert sum(r.url.params.get("action") == "wbsearchentities" for r in requests) == 1


def test_a_reply_that_is_not_json_means_no_photo_not_a_crash():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"<html>busy</html>")))
    assert lookup("Divididos", client) is None
