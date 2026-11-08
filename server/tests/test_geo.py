from app.scrapers.geo import city_name, region_code


def test_city_by_comuna_or_explicit_name():
    assert region_code("Comuna 14", "Buenos Aires") == "AR-C"
    assert region_code("Comuna 15", "Ciudad Autónoma de Buenos Aires") == "AR-C"


def test_city_written_as_the_locality_with_no_region():
    # Movistar Arena publishes the city as the locality and no region at all
    assert region_code("Ciudad Autónoma de Buenos Aires", "") == "AR-C"
    assert region_code("Buenos Aires", "") == "AR-C"


def test_province_and_other_provinces():
    assert region_code("La Plata", "Buenos Aires") == "AR-B"
    assert region_code("Quilmes", "Provincia de Buenos Aires") == "AR-B"
    assert region_code("Mendoza", "") == "AR-M"
    assert region_code("Confluencia", "Neuquén") == "AR-Q"


def test_unknown_place_has_no_region():
    assert region_code("Springfield", "") is None


def test_city_name_replaces_the_comuna():
    assert city_name("Comuna 14", "AR-C") == "Buenos Aires"
    assert city_name("La Plata", "AR-B") == "La Plata"
