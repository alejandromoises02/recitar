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
    r"^(.*?\S)\s+(?:presentan?|cierran?|celebran?|vuelven?|regresan?|despiden?|en vivo)\b.*$", re.IGNORECASE
)
# The last " en <something>": cut only when <something> is the show's own venue or city (see _is_place).
_EN_TAIL = re.compile(r"^(.*\S)\s+en\s+(.+)$", re.IGNORECASE)
# "5-12", "29 NOV", "18 dic.": the date is stored apart.
_DATE_SUFFIX = re.compile(
    r"^(.*\S)\s+\d{1,2}(?:-\d{1,2}|\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic)[a-z]*\.?)$",
    re.IGNORECASE,
)
_DANGLING = " -–:|"
# Other names people use for the city of Buenos Aires.
_CITY_ALIASES = ("capital federal", "caba", "bs as", "bsas")
# Words that stay lower case inside a title set in title case (never the first word).
_SMALL_WORDS = {"a", "al", "de", "del", "el", "en", "la", "las", "lo", "los", "y", "e", "o", "u", "un", "una",
                "con", "por", "para", "sin", "the", "of", "and", "x"}
_VOWELS = set("aeiouyáéíóúü")

# A night named after the party, not an act: no artist.
_PARTY = re.compile(
    r"\b(?:fiesta|party|ciclo|club|noche|night|open air|vol|festival|lollapalooza)\b|fest\b", re.IGNORECASE
)
# A yearly edition ("Quilmes Rock 2027", "Primavera Sound '26") is a line-up, not one act.
_EDITION = re.compile(r"\b(?:19|20)\d{2}\b|'\d{2}\b")
_TRIBUTE = re.compile(r"^(.+?)\s+por\s+\S", re.IGNORECASE)  # "Serú Girán por Lebón y Aznar"
_SEVERAL_ACTS = re.compile(r"\s+(?:\+|&|•)\s+|,\s+")
_COLON_SOLOIST = re.compile(r"^([^()–\-]+?)\s*\([^)]*\)\s*[–\-]")  # "Lovro Pogorelić (piano) – ..."


@dataclass(frozen=True)
class TidyTitle:
    display: str  # what the app shows: every word of the title, only tidied in looks (case, spaces, "+18")
    name: str  # the title without place, date and filler: the step the artist is read from
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


def _display(title: str, source: str) -> str:
    """The organiser's title, every word kept: only spaces, the adults-only note and shouting are tidied.
    Shouting is judged on the act, before the " en <place>" Livepass and Venti add."""
    text = " ".join(_ADULTS_ONLY.sub("", title).split())
    text = re.sub(r"\?en\s", " en ", text) if source in _PLACE_SUFFIX_SOURCES else text
    match = _PLACE_SUFFIX.match(text) if source in _PLACE_SUFFIX_SOURCES else None
    act = match.group(1).rstrip(" ?") if match else text
    text = _title_case(text) if _is_shouted(act) else text
    return text or " ".join(title.split())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", fold(text)) if w not in _SMALL_WORDS}


def _is_place(tail: str, venue: set[str], city: set[str], city_ok: bool) -> bool:
    """`tail` names the show's venue (some of its words, plus maybe the city: "Kabryl - Necochea").
    With `city_ok` the city alone also counts; that is for the artist only, since "Noche en Buenos
    Aires" can be a show's real name."""
    words = _words(tail)
    if not words or not words <= venue | city:
        return city_ok and fold(tail).strip() in _CITY_ALIASES
    return city_ok or bool(words & venue)


def _cut_place_and_date(name: str, venue: set[str], city: set[str], city_ok: bool) -> str:
    while True:
        if match := _DATE_SUFFIX.match(name):
            name = match.group(1)
        elif (match := _EN_TAIL.match(name)) and _is_place(match.group(2), venue, city, city_ok):
            name = match.group(1)
        else:
            return name


def _name(title: str, source: str, venue: set[str], city: set[str]) -> str:
    name = " ".join(_ADULTS_ONLY.sub("", title).split())
    if source in _PLACE_SUFFIX_SOURCES and (match := _PLACE_SUFFIX.match(name)):
        name = match.group(1).rstrip(" ?")
    # Judged before the cuts below: "LAUTA 29 NOV" is shouted, while "LAUTA" alone may be a name as written.
    shouted = _is_shouted(name)
    name = _cut_place_and_date(name, venue, city, city_ok=False)
    if match := _FILLER.match(name):
        name = match.group(1)
    shouted = shouted or _is_shouted(name)
    name = name.rstrip(_DANGLING)
    name = _title_case(name) if shouted else name
    return name or " ".join(title.split())  # never empty: fall back to the source's words


def _artist(name: str, title: str, source: str, venue: set[str], city: set[str]) -> str | None:
    if source == "colon":  # works and programmes, except "Soloist (instrument) – ..."
        match = _COLON_SOLOIST.match(title)
        return match.group(1).strip() if match else None
    name = _cut_place_and_date(name, venue, city, city_ok=True)
    if _PARTY.search(name):
        return None
    artist = re.split(r" [-–] |: ", name)[0]  # "X - subtitle", "X – Tour 2026", "X: Solo Piano"
    if match := _TRIBUTE.match(artist):
        artist = match.group(1)
    artist = _SEVERAL_ACTS.split(artist)[0].strip(_DANGLING + " ")
    return None if not artist or _EDITION.search(artist) else artist


def tidy_title(title: str, source: str, venue: str | None = None, city: str | None = None) -> TidyTitle:
    """`source` is the first part of the event id (colon, livepass, movistar, venti...). `venue` and
    `city` are the show's own, stored apart: a title that repeats them ("Ivan Noble en Vorterix")
    loses them."""
    venue_words, city_words = _words(venue or ""), _words(city or "")
    name = _name(title, source, venue_words, city_words)
    return TidyTitle(
        display=_display(title, source), name=name, artist=_artist(name, title, source, venue_words, city_words)
    )
