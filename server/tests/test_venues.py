import pytest

from app.scrapers.venues import VENUE_TO_BE_CONFIRMED, canonical_venue


@pytest.mark.parametrize("name", ["Niceto Club", "Niceto Bar", "Humboldt | Niceto Club"])
def test_every_niceto_room_is_one_venue(name):
    assert canonical_venue(name) == "Niceto Club"


def test_aliases_match_ignoring_case_accents_and_extra_spaces():
    assert canonical_venue("  humboldt |  NICETO club ") == "Niceto Club"
    assert canonical_venue("Nicetó Bar") == "Niceto Club"


@pytest.mark.parametrize("name", ["Teatro Colón", "Movistar Arena", "Club Re", ""])
def test_a_venue_without_aliases_keeps_its_name(name):
    assert canonical_venue(name) == name


def test_a_name_that_only_contains_an_alias_is_not_renamed():
    assert canonical_venue("Niceto Bar Pop-up en Palermo") == "Niceto Bar Pop-up en Palermo"


@pytest.mark.parametrize("name", ["Argentina", "A confirmar", "Lugar a confirmar", "A definir", "Por confirmar", "TBA"])
def test_a_placeholder_venue_is_a_venue_to_be_confirmed(name):
    assert canonical_venue(name) == VENUE_TO_BE_CONFIRMED == "Lugar a confirmar"  # Quilmes Rock's venue is "Argentina"


@pytest.mark.parametrize("name, city", [
    ("Vorterix", "Mar del Plata"),  # Articket
    ("Teatro Vorterix Mar del Plata", "Mar del Plata"),  # All Access
    ("Teatro Vorterix Mar del Plata", None),
])
def test_vorterix_in_mar_del_plata_is_told_apart_from_the_one_in_the_city(name, city):
    assert canonical_venue(name, city) == "Teatro Vorterix (Mar del Plata)"


@pytest.mark.parametrize("name, city", [("Teatro Vorterix", "Buenos Aires"), ("Vorterix", "Buenos Aires"), ("Vorterix", None)])
def test_vorterix_elsewhere_is_the_one_in_the_city(name, city):
    assert canonical_venue(name, city) == "Teatro Vorterix"
