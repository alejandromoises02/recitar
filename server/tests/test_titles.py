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
        got = getattr(tidy_title(case["title"], case["source"], case.get("venue"), case.get("city")), field)
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


# --- the place, dates and editions (the show's own venue and city are known) ----------------------

@pytest.mark.parametrize("source,title,venue,name", [
    ("articket", "IVAN NOBLE EN VORTERIX", "Teatro Vorterix (Mar del Plata)", "Ivan Noble"),
    ("allaccess", "DISCONTINUOS EN THE ROXY LIVE", "The Roxy Live", "Discontinuos"),
    ("enigma", "ALEX ANWANDTER EN DESEO CLUB", "Deseo Club", "Alex Anwandter"),
    ("articket", "Los Totora en Kabryl - Necochea", "Kabryl", "Los Totora"),
])
def test_a_trailing_en_that_names_the_show_venue_is_cut_from_any_source(source, title, venue, name):
    tidy = tidy_title(title, source, venue=venue, city="Necochea")
    assert (tidy.name, tidy.artist) == (name, name)


@pytest.mark.parametrize("title", ["Elvis En 360º", "Nestor en Bloque", "LOW en ROCK N' GASOLINE"])
def test_an_en_that_is_not_the_venue_stays(title):
    assert tidy_title(title, "tuentrada", venue="Rondeman Abasto", city="Buenos Aires").name == title


def test_the_city_is_cut_from_the_artist_but_not_from_the_name():
    tidy = tidy_title("CRUZANDO EL CHARCO EN BUENOS AIRES", "allaccess", venue="Teatro Vorterix", city="Buenos Aires")
    assert (tidy.name, tidy.artist) == ("Cruzando el Charco en Buenos Aires", "Cruzando el Charco")


@pytest.mark.parametrize("source,title,venue,city,name", [
    ("articket", "SKAY Y LOS FAKIRES EN MAR DEL PLATA 5-12", "PLAZA DE LA MÚSICA", "Mar del Plata", "Skay y los Fakires en Mar del Plata"),
    ("venti", "LAUTA 29 NOV en Niceto Club (+18años)", "Niceto Club", "Buenos Aires", "Lauta"),
    ("venti", "OCTAFONIC 18 DIC en Niceto Club (+18 años)", "Niceto Club", "Buenos Aires", "Octafonic"),
])
def test_a_trailing_date_is_cut(source, title, venue, city, name):
    assert tidy_title(title, source, venue=venue, city=city).name == name


def test_skay_loses_both_the_date_and_the_city_as_artist():
    tidy = tidy_title("SKAY Y LOS FAKIRES EN MAR DEL PLATA 5-12", "articket", venue="PLAZA DE LA MÚSICA", city="Mar del Plata")
    assert tidy.artist == "Skay y los Fakires"


@pytest.mark.parametrize("title,name", [
    ("MUGRE DESPIDE EL AÑO", "Mugre"),
    ("ORATE - PRESENTA SU NUEVO ALBUM inv ABISMAL", "Orate"),
])
def test_more_filler_and_a_dangling_dash_are_cut(title, name):
    assert tidy_title(title, "allaccess").name == name


def test_an_en_dash_subtitle_is_not_part_of_the_artist():
    assert tidy_title("LAGOS – BUENOS AIRES – TOUR 2026", "allaccess").artist == "Lagos"


@pytest.mark.parametrize("title", [
    "LOLLAPALOOZA 2027", "Quilmes Rock 2027", "BUENA LA ACTITUD ROCK 2026 Presenta VINILO 106", "PopFest 101.5",
    "Festival La Porteña", "Primavera Sound Buenos Aires '26", "NEUROFEST",
])
def test_festivals_and_yearly_editions_have_no_artist(title):
    assert tidy_title(title, "allaccess").artist is None


# --- display: what the app shows is the organiser's title, only tidied in looks ----------------

@pytest.mark.parametrize("source,title,display", [
    ("articket", "IVAN NOBLE EN VORTERIX", "Ivan Noble en Vorterix"),
    ("venti", "Barbi Recanati en Niceto Club (+18 años)", "Barbi Recanati en Niceto Club"),
    ("livepass", "TAN BIONICA en Estadio Uno", "Tan Bionica en Estadio Uno"),
    ("livepass", "A PERFECT CIRCLE + PUSCIFER?en Buenos Aires", "A Perfect Circle + Puscifer en Buenos Aires"),
    ("allaccess", "MUGRE DESPIDE EL AÑO EN CAPITAL FEDERAL", "Mugre Despide el Año en Capital Federal"),
    ("movistar", "Una noche mágica con Luis Miguel", "Una noche mágica con Luis Miguel"),
    ("movistar", "  Luis   Fonsi ", "Luis Fonsi"),
])
def test_the_display_keeps_every_word_of_the_title(source, title, display):
    assert tidy_title(title, source, venue="Teatro Vorterix", city="Buenos Aires").display == display


def test_the_display_of_a_title_that_tidies_to_nothing_is_the_original():
    assert tidy_title("(+18 años)", "venti").display == "(+18 años)"


def test_the_show_name_the_api_sends_is_the_display():
    from datetime import datetime, timezone

    from app.domain.event import Event, TicketLink

    event = Event(
        id="articket-ivan-noble-20270110T2100", category="concert", title="IVAN NOBLE EN VORTERIX",
        venue="Teatro Vorterix (Mar del Plata)", starts_at=datetime(2027, 1, 11, 0, 0, tzinfo=timezone.utc),
        ticket_links=[TicketLink(vendor="Articket", url="https://articket.com.ar/x")], source_url="https://articket.com.ar/x",
        updated_at=datetime(2026, 11, 23, tzinfo=timezone.utc),
    )
    assert event.name == "Ivan Noble en Vorterix"
