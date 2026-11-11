"""One name per venue, whatever the source calls it.

Sources name the same place in different ways (Venti lists Niceto as "Niceto Club",
"Niceto Bar" and "Humboldt | Niceto Club"). Filtering by venue needs a single name, so known
variants are mapped to the canonical one. Matching is exact after folding case, accents and
spacing: a name that merely contains an alias is left alone.
"""

from app.scrapers.geo import plain

CANONICAL_NAMES: dict[str, list[str]] = {
    # Niceto's rooms (club, bar and the Humboldt street side) are one venue for users.
    "Niceto Club": ["Niceto Club", "Niceto Bar", "Humboldt | Niceto Club"],
}

_ALIASES = {plain(alias): name for name, aliases in CANONICAL_NAMES.items() for alias in aliases}


def canonical_venue(name: str) -> str:
    return _ALIASES.get(plain(name), name)
