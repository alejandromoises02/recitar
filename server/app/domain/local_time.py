"""Days are Buenos Aires days. Times are stored in UTC, so a day is turned into a UTC window.

A show on Saturday at 22:00 in Buenos Aires is stored as Sunday 01:00 UTC; it must still count as
Saturday. Converting through the time zone (not a fixed -3 offset) keeps this right if Argentina
ever changes its offset again.
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")


def start_of_day(day: date) -> datetime:
    """The UTC instant when `day` begins in Buenos Aires."""
    return datetime.combine(day, time.min, tzinfo=BUENOS_AIRES).astimezone(timezone.utc)


def day_window(first: date | None, last: date | None) -> tuple[datetime | None, datetime | None]:
    """[start, end) in UTC covering the Buenos Aires days `first` to `last`, both included.
    A missing side stays open."""
    start = start_of_day(first) if first else None
    end = start_of_day(last + timedelta(days=1)) if last else None
    return start, end
