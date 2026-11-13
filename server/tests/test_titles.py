import json
from pathlib import Path

import pytest

from app.domain.titles import fold, tidy_title

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "titles_golden.json").read_text())


# --- one test per rule ---------------------------------------------------------------------------

@pytest.mark.parametrize("source,title,name", [
    ("livepass", "TAN BIONICA en Estadio Uno", "Tan Bionica"),
    ("livepass", "LUZ GAGGI en el Teatro Opera LP", "Luz Gaggi"),
    ("livepass", "A PERFECT CIRCLE + PUSCIFER?en Buenos Aires", "A Perfect Circle + Puscifer"),
    ("venti", "Catalina Ammaturo en Niceto Club (+18 años)", "Catalina Ammaturo"),
    ("venti", "OEISIS - Familiar vibes in the area en Niceto Club (+18 años)", "OEISIS - Familiar vibes in the area"),
])
def test_livepass_and_venti_lose_the_trailing_place(source, title, name):
    assert tidy_title(title, source).name == name


@pytest.mark.parametrize("source,title", [
    ("colon", "Mozart en Viena"),
    ("movistar", "Noche en Buenos Aires"),
])
def test_other_sources_keep_en_because_it_can_be_part_of_the_name(source, title):
    assert tidy_title(title, source).name == title


def test_the_adults_only_note_is_dropped_even_without_a_place():
    assert tidy_title("Mi Amigo Invencible Regresa a Niceto Club (+18 años)", "venti").name == "Mi Amigo Invencible"


@pytest.mark.parametrize("title,name", [
    ("EL MATO A UN POLICIA MOTORIZADO", "El Mato a un Policia Motorizado"),
    ("LA DANZA DE LAS BESTIAS + PLAYA DEL KARMA", "La Danza de las Bestias + Playa del Karma"),
    ("RE-UNIÓN NEGRA", "Re-Unión Negra"),
    ("LUCHO SSJ", "Lucho SSJ"),  # short all-caps words may be initials: kept
    ("CATTO EYEWEAR SS27", "Catto Eyewear SS27"),  # words with digits: kept
])
def test_a_shouted_title_is_set_in_title_case(title, name):
    assert tidy_title(title, "movistar").name == name


@pytest.mark.parametrize("title", ["BABYMETAL", "Ana Gabriel", "Reich/Richter", "IVAN SALO & Los Paracaidistas"])
def test_single_words_and_titles_with_lowercase_are_left_alone(title):
    assert tidy_title(title, "movistar").name == title


@pytest.mark.parametrize("title,name", [
    ("SuperVos cierra el año", "SuperVos"),
    ("Gallo Criollo celebra su 1er año", "Gallo Criollo"),
    ("LAGRIMITAS presenta en vivo su nueva etapa", "LAGRIMITAS"),
    ("Santiago Cruz vuelve a la Argentina", "Santiago Cruz"),
    ("CHAPEAUX en vivo", "CHAPEAUX"),
])
def test_known_filler_phrases_are_cut(title, name):
    assert tidy_title(title, "movistar").name == name


def test_spaces_are_tidied():
    assert tidy_title("  Luis   Fonsi ", "movistar").name == "Luis Fonsi"


# --- artist ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("source,title,artist", [
    ("movistar", "Andres Calamaro", "Andres Calamaro"),
    ("livepass", "BABASONICOS en el Hipodromo de La Plata", "BABASONICOS"),
    ("venti", "JULI JELEN en Niceto Bar", "Juli Jelen"),
])
def test_a_plain_name_is_the_artist(source, title, artist):
    assert tidy_title(title, source).artist == artist


@pytest.mark.parametrize("title,artist", [
    ("A PERFECT CIRCLE + PUSCIFER", "A Perfect Circle"),
    ("Nora Sarmoria & Victoria Zotalis", "Nora Sarmoria"),
    ("Montse • Fredrik Svabø • Thea Wang", "Montse"),
])
def test_with_several_acts_the_first_one_is_the_artist(title, artist):
    assert tidy_title(title, "livepass").artist == artist


def test_a_tribute_names_the_band_paid_tribute_to():
    assert tidy_title("SERU GIRAN POR LEBÓN Y AZNAR", "movistar").artist == "Seru Giran"


def test_a_subtitle_after_a_dash_is_not_part_of_the_artist():
    assert tidy_title("OEISIS - Familiar vibes in the area en Niceto Club", "venti").artist == "OEISIS"


@pytest.mark.parametrize("title", [
    "FIESTA MERMELADA - NACIONAL en Humboldt | Niceto Club", "Random Fiesta en Niceto Club", "CICLO DESORDEN en Niceto Bar",
    "NOCHE PANTERA en Niceto Bar", "SELF-TITLED x FOUND - OPEN AIR en Niceto Bar", "Club 69 | 14 NOV en Niceto Club",
    "Reggaeton Night Vol ll en Niceto Bar",
])
def test_parties_have_no_artist(title):
    assert tidy_title(title, "venti").artist is None


@pytest.mark.parametrize("title", ["El cascanueces", "Die Walküre", "Mozart y Beethoven: obras para clarinete y cuerdas"])
def test_colon_works_have_no_artist(title):
    assert tidy_title(title, "colon").artist is None


def test_a_colon_soloist_is_the_artist():
    assert tidy_title("Lovro Pogorelić (piano) – Festival Chopiniana", "colon").artist == "Lovro Pogorelić"


def test_an_unknown_source_still_tidies_without_guessing_an_artist_rule():
    assert tidy_title("ED SHEERAN", "nueva").name == "Ed Sheeran"


def test_fold_ignores_case_and_accents():
    assert fold("Usted Señálemelo") == fold("USTED SENALEMELO")


# --- the golden list: real titles with the result a person would choose ---------------------------

def _accuracy(field: str) -> tuple[float, list[str]]:
    misses = []
    for case in GOLDEN:
        got = getattr(tidy_title(case["title"], case["source"]), field)
        want = case[field]
        if (got is None) != (want is None) or (got is not None and fold(got) != fold(want)):
            misses.append(f"{case['source']}: {case['title']!r} -> {got!r}, want {want!r}")
    return 1 - len(misses) / len(GOLDEN), misses


def test_the_golden_list_has_every_source():
    assert {c["source"] for c in GOLDEN} == {"colon", "livepass", "movistar", "venti"}
    assert len(GOLDEN) >= 50


@pytest.mark.parametrize("field,minimum", [("name", 0.90), ("artist", 0.80)])
def test_golden_accuracy_ignoring_case_and_accents(field, minimum):
    accuracy, misses = _accuracy(field)
    print(f"\n{field}: {accuracy:.0%} of {len(GOLDEN)}\n  " + "\n  ".join(misses))
    assert accuracy >= minimum, "\n".join(misses)


def test_y_counts_as_a_vowel_so_long_words_are_not_taken_for_initials():
    assert tidy_title("VALERIA LYNCH", "movistar").name == "Valeria Lynch"


def test_a_subtitle_after_a_colon_is_not_part_of_the_artist():
    assert tidy_title("Ludovico Einaudi: Solo Piano en el Teatro Colon", "livepass").artist == "Ludovico Einaudi"


def test_a_title_that_tidies_to_nothing_keeps_the_original():
    assert tidy_title("(+18 años)", "venti").name == "(+18 años)"
