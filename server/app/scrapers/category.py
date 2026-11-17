"""Provisional event category, shared by the sources that do not say what kind of event it is.

Replaced by LLM classification (see the "LLM extraction" task). Until then: all-night events
start at 23:59 and end at dawn, and some titles say it outright; a title that names another act
("Tributo a Soda", "DM Experience", "The Beatles in my life") is a tribute; anything else at a
concert venue is assumed to be a concert. Words that also name original acts were left out:
"por" ("Seru Girán por Lebón y Aznar" are the band's own members) and "plays" ("Quintet plays Ballads").

A tribute is a band that lives off playing another act's songs, usually in small venues. An orchestral
homage ("Homenaje Sinfónico Ennio Morricone") is a produced show people go to as a concert, so it stays
a concert. Decided with the user on 2026-11-17: once a show can have more than one category (with LLM
classification), these homages should appear under both concerts and tributes.
"""

import re
from datetime import datetime

from app.domain.event import EventCategory
from app.scrapers.geo import plain

_NIGHT_START = (23, 59)
_PARTY_WORDS = ("fiesta", "noche")
_TRIBUTE = re.compile(
    r"\b(tributo|tribute|homenaje|covers?|experience|celebration|revival|beatles)\b"
    r"|\bcanta (a|al|el|la|los|las)\b"
)
_ORCHESTRAL = re.compile(r"\b(sinfonic[oa]s?|orquesta|filarmonica)\b")


def is_tribute(title: str) -> bool:
    text = plain(title)
    return _TRIBUTE.search(text) is not None and _ORCHESTRAL.search(text) is None


def provisional_category(title: str, starts_at: datetime) -> EventCategory:
    if (starts_at.hour, starts_at.minute) == _NIGHT_START:
        return "other"
    if any(word in plain(title) for word in _PARTY_WORDS):
        return "other"
    return "tribute" if is_tribute(title) else "concert"
