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
