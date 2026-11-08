"""Location normalisation shared by every scraper, so all sources fill city/region/country alike."""

import re
import unicodedata

CITY_OF_BUENOS_AIRES = "AR-C"
BUENOS_AIRES_CITY_NAME = "Buenos Aires"

_COMUNA = re.compile(r"^comuna\s+\d+", re.I)

# ISO 3166-2:AR, keyed by accent-free lowercase province name.
_PROVINCES = {
    "salta": "AR-A", "buenos aires": "AR-B", "san luis": "AR-D", "entre rios": "AR-E",
    "la rioja": "AR-F", "santiago del estero": "AR-G", "chaco": "AR-H", "san juan": "AR-J",
    "catamarca": "AR-K", "la pampa": "AR-L", "mendoza": "AR-M", "misiones": "AR-N",
    "formosa": "AR-P", "neuquen": "AR-Q", "rio negro": "AR-R", "santa fe": "AR-S",
    "tucuman": "AR-T", "chubut": "AR-U", "tierra del fuego": "AR-V", "corrientes": "AR-W",
    "cordoba": "AR-X", "jujuy": "AR-Y", "santa cruz": "AR-Z",
}


def plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split())


def region_code(locality: str, region: str) -> str | None:
    """ISO region of an Argentine venue, from whatever the source gives.

    Sources write this inconsistently: "Buenos Aires" can mean the city or the province,
    so the city is recognised by "Comuna N", its explicit name, or a bare "Buenos Aires"
    locality with no region. Without a region the locality is tried as a province name.
    """
    place, area = plain(locality), plain(region)
    if _COMUNA.match(place) or "ciudad autonoma" in place + " " + area or area == "capital federal":
        return CITY_OF_BUENOS_AIRES
    if not area and place in {"buenos aires", "caba", "capital federal"}:
        return CITY_OF_BUENOS_AIRES
    if area.startswith("provincia de "):
        area = area[len("provincia de "):]
    return _PROVINCES.get(area or place)


def city_name(locality: str | None, region: str | None) -> str | None:
    """Sources give a comuna ("Comuna 14") for the city; store the city name instead."""
    return BUENOS_AIRES_CITY_NAME if region == CITY_OF_BUENOS_AIRES else locality
