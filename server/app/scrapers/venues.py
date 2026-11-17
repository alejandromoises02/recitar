"""One name per venue, whatever the source calls it.

Sources name the same place in different ways (Venti lists Niceto as "Niceto Club",
"Niceto Bar" and "Humboldt | Niceto Club"). Filtering by venue needs a single name, so known
variants are mapped to the canonical one. Matching is exact after folding case, accents and
spacing: a name that merely contains an alias is left alone.

A source that does not know the venue yet writes a placeholder instead ("A confirmar", or a whole
country: Enigma lists Quilmes Rock 2027 at "Argentina"); all of them become one name.
"""

from app.domain.event import VENUE_TO_BE_CONFIRMED
from app.scrapers.geo import plain

CANONICAL_NAMES: dict[str, list[str]] = {
    VENUE_TO_BE_CONFIRMED: [
        "Lugar a confirmar", "A confirmar", "Por confirmar", "Lugar a definir", "A definir", "TBA", "Argentina",
    ],
    # Niceto's rooms (club, bar and the Humboldt street side) are one venue for users.
    "Niceto Club": ["Niceto Club", "Niceto Bar", "Humboldt | Niceto Club"],
}

_ALIASES = {plain(alias): name for name, aliases in CANONICAL_NAMES.items() for alias in aliases}


def canonical_venue(name: str) -> str:
    return _ALIASES.get(plain(name), name)
