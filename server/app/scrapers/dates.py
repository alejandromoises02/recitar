def time_given(start_date: str) -> bool:
    """A schema.org startDate is ISO 8601: a day ("2026-11-29") or a day and time ("2026-11-29T21:00-03:00").
    A day alone parses as midnight, which is not when the show starts."""
    return "T" in start_date
