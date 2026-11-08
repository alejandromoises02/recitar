from datetime import datetime
from zoneinfo import ZoneInfo

from app.scrapers.category import provisional_category

BA = ZoneInfo("America/Argentina/Buenos_Aires")


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 20, hour, minute, tzinfo=BA)


def test_evening_show_is_a_concert():
    assert provisional_category("María Becerra", at(21)) == "concert"


def test_all_night_start_is_not_a_concert():
    assert provisional_category("Kybba en Niceto Club", at(23, 59)) == "other"


def test_party_words_in_the_title_are_not_a_concert():
    assert provisional_category("Fiesta ¡FA!", at(21)) == "other"
    assert provisional_category("NOCHE PANTERA", at(21)) == "other"
    assert provisional_category("TRASNOCHE", at(21)) == "other"
