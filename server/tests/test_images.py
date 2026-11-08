from app.scrapers.images import first_image_url, source_image


def test_a_plain_url():
    assert first_image_url("https://x.com/a.jpg") == "https://x.com/a.jpg"


def test_json_ld_allows_a_list_or_an_image_object():
    assert first_image_url(["https://x.com/a.jpg", "https://x.com/b.jpg"]) == "https://x.com/a.jpg"
    assert first_image_url({"@type": "ImageObject", "url": "https://x.com/a.jpg"}) == "https://x.com/a.jpg"


def test_missing_or_unusable_values_give_none():
    for value in (None, "", [], {}, 42, "not a url", "/relative/a.jpg"):
        assert first_image_url(value) is None


def test_source_image_marks_the_origin():
    assert source_image("https://x.com/a.jpg") == {"image_url": "https://x.com/a.jpg", "image_origin": "source"}


def test_source_image_without_url_adds_nothing():
    assert source_image(None) == {}
