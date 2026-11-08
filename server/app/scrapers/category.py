"""Provisional event category, shared by the sources that do not say what kind of event it is.

Replaced by LLM classification (see the "LLM extraction" task). Until then: all-night events
start at 23:59 and end at dawn, and some titles say it outright; anything else at a
concert venue is assumed to be a concert.
"""

from datetime import datetime

from app.domain.event import EventCategory
from app.scrapers.geo import plain

_NIGHT_START = (23, 59)
_PARTY_WORDS = ("fiesta", "noche")


def provisional_category(title: str, starts_at: datetime) -> EventCategory:
    if (starts_at.hour, starts_at.minute) == _NIGHT_START:
        return "other"
    if any(word in plain(title) for word in _PARTY_WORDS):
        return "other"
    return "concert"
