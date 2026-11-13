"""A readable name and, when the title says it, the artist, from a show title as each source
publishes it. Plain rules, no AI: tests/fixtures/titles_golden.json measures how often they are
right on real titles, and is what a future LLM extractor would have to beat.

The rules never invent: when the artist cannot be read with confidence it stays None, and the
client falls back to the name.
"""

import re
import unicodedata
from dataclasses import dataclass

# Livepass and Venti always end the title with " en <place>" (the place is stored apart, and often
# under another name, e.g. "en CCNU" for Centro Cultural Nueva Uriarte). Elsewhere "en" can be part
# of the name, so it is kept.
_PLACE_SUFFIX_SOURCES = {"livepass", "venti"}
_PLACE_SUFFIX = re.compile(r"^(.*\S)[\s?]+en\s+\S.*$", re.IGNORECASE)
_ADULTS_ONLY = re.compile(r"\s*\(\s*\+\s*18\s*años?\s*\)", re.IGNORECASE)
# Phrases after the act's name that say what the night is about, not who plays.
_FILLER = re.compile(
    r"^(.*?\S)\s+(?:presentan?|cierran?|celebran?|vuelven?|regresan?|en vivo)\b.*$", re.IGNORECASE
)
# Words that stay lower case inside a title set in title case (never the first word).
_SMALL_WORDS = {"a", "al", "de", "del", "el", "la", "las", "lo", "los", "y", "e", "o", "u", "un", "una",
                "con", "por", "para", "sin", "the", "of", "and", "x"}
_VOWELS = set("aeiouyáéíóúü")

# A night named after the party, not an act: no artist.
_PARTY = re.compile(r"\b(?:fiesta|party|ciclo|club|noche|night|open air|vol)\b", re.IGNORECASE)
_TRIBUTE = re.compile(r"^(.+?)\s+por\s+\S", re.IGNORECASE)  # "Serú Girán por Lebón y Aznar"
_SEVERAL_ACTS = re.compile(r"\s+(?:\+|&|•)\s+|,\s+")
_COLON_SOLOIST = re.compile(r"^([^()–\-]+?)\s*\([^)]*\)\s*[–\-]")  # "Lovro Pogorelić (piano) – ..."


@dataclass(frozen=True)
class TidyTitle:
    name: str  # what to show; the verbatim title stays in Event.title
    artist: str | None  # who plays, to look up (Spotify, Wikimedia); None when not clear


def fold(text: str) -> str:
    """Lower case without accents, to compare names the way people read them."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def _is_shouted(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters) and " " in text


def _word_case(word: str, first: bool) -> str:
    if any(c.isdigit() for c in word):
        return word  # SS27, 90S: codes, not words
    if "-" in word:
        return "-".join(_word_case(part, first) for part in word.split("-"))
    lower = word.lower()
    if not first and lower in _SMALL_WORDS:
        return lower
    if len(word) <= 3 and not _VOWELS & set(lower):
        return word  # SSJ, LP: initials
    return word[:1].upper() + word[1:].lower()


def _title_case(text: str) -> str:
    return " ".join(_word_case(word, i == 0) for i, word in enumerate(text.split(" ")))


def _name(title: str, source: str) -> str:
    name = " ".join(_ADULTS_ONLY.sub("", title).split())
    if source in _PLACE_SUFFIX_SOURCES and (match := _PLACE_SUFFIX.match(name)):
        name = match.group(1).rstrip(" ?")
    if match := _FILLER.match(name):
        name = match.group(1)
    name = _title_case(name) if _is_shouted(name) else name
    return name or " ".join(title.split())  # never empty: fall back to the source's words


def _artist(name: str, title: str, source: str) -> str | None:
    if source == "colon":  # works and programmes, except "Soloist (instrument) – ..."
        match = _COLON_SOLOIST.match(title)
        return match.group(1).strip() if match else None
    if _PARTY.search(name):
        return None
    artist = re.split(r" - |: ", name)[0]  # "X - subtitle", "X: Solo Piano"
    if match := _TRIBUTE.match(artist):
        artist = match.group(1)
    return _SEVERAL_ACTS.split(artist)[0].strip() or None


def tidy_title(title: str, source: str) -> TidyTitle:
    """`source` is the first part of the event id (colon, livepass, movistar, venti)."""
    name = _name(title, source)
    return TidyTitle(name=name, artist=_artist(name, title, source))
