"""One name per venue, whatever the source calls it.

Sources name the same place in different ways (Venti lists Niceto as "Niceto Club",
"Niceto Bar" and "Humboldt | Niceto Club"). Filtering by venue needs a single name, so known
variants are mapped to the canonical one. Matching is exact after folding case, accents and
spacing: a name that merely contains an alias is left alone.

The same name can also stand for two venues in different cities (Articket's "Vorterix" is the one
in Mar del Plata), so those are told apart by the city. A source that does not know the venue yet writes a placeholder instead ("A confirmar", or a whole
country: Enigma lists Quilmes Rock 2027 at "Argentina"); all of them become one name.
"""

from app.domain.event import VENUE_TO_BE_CONFIRMED
from app.scrapers.geo import plain

CANONICAL_NAMES: dict[str, list[str]] = {
    VENUE_TO_BE_CONFIRMED: [
        "Lugar a confirmar", "A confirmar", "Por confirmar", "Lugar a definir", "A definir", "TBA", "Argentina",
    ],
    "Teatro Vorterix": ["Teatro Vorterix", "Vorterix"],
    "Teatro Vorterix (Mar del Plata)": ["Teatro Vorterix Mar del Plata", "Teatro Vorterix (Mar del Plata)"],
    # Niceto's rooms (club, bar and the Humboldt street side) are one venue for users.
    "Niceto Club": ["Niceto Club", "Niceto Bar", "Humboldt | Niceto Club"],
    # Ticketek, which also sells there, writes it "Groove (Palermo)".
    "Palermo Groove": ["Palermo Groove", "Groove (Palermo)"],
}

# A name that stands for different venues depending on the city: (name, city) -> canonical name.
# Articket writes the Mar del Plata Vorterix as plain "Vorterix", the name of the one in the city.
BY_CITY: dict[tuple[str, str], str] = {
    ("Vorterix", "Mar del Plata"): "Teatro Vorterix (Mar del Plata)",
    ("Teatro Vorterix", "Mar del Plata"): "Teatro Vorterix (Mar del Plata)",
}

_ALIASES = {plain(alias): name for name, aliases in CANONICAL_NAMES.items() for alias in aliases}
_BY_CITY = {(plain(name), plain(city)): canonical for (name, city), canonical in BY_CITY.items()}


def canonical_venue(name: str, city: str | None = None) -> str:
    """The venue's one name; `city` tells apart venues that sources name alike in different cities."""
    return _BY_CITY.get((plain(name), plain(city or ""))) or _ALIASES.get(plain(name), name)
