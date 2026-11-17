from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

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


@pytest.mark.parametrize("title", [
    "CAMINO STEREO - Tributo a Soda & Cerati",
    "Katseye: The tribute experience",
    "DEL LADO B - HOMENAJE AL ROCK NACIONAL",
    "DM Experience",
    "QUEEN CELEBRATION XP",
    "JAVIER PARISI: THE BEATLES IN MY LIFE",
    "Show de covers de Los Redondos",
    "EL NATTY COMBO - 'Sergio Colombo canta Los Fundamentalistas'",
])
def test_a_title_naming_another_act_is_a_tribute(title):
    assert provisional_category(title, at(21)) == "tribute"


@pytest.mark.parametrize("title", [
    "SERU GIRAN POR LEBON Y AZNAR",  # the band's own members
    "Caleb Monte Quintet plays Ballads en CCNU",
    "Cantando bajo la lluvia",
])
def test_original_acts_stay_concerts(title):
    assert provisional_category(title, at(21)) == "concert"


def test_a_tribute_party_is_still_a_party():
    assert provisional_category("Fiesta tributo a los 90s", at(21)) == "other"
    assert provisional_category("Tributo a Ricky Martin", at(23, 59)) == "other"


@pytest.mark.parametrize("title", [
    "Homenaje Sinfónico Ennio Morricone",
    "María Elena Walsh Sinfónico",
    "Tributo a Queen con orquesta",
])
def test_an_orchestral_homage_is_a_concert(title):
    assert provisional_category(title, at(21)) == "concert"
