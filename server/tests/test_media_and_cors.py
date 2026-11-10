from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.images.copy import IMAGES_DIR, MEDIA_PREFIX
from app.main import DEFAULT_CORS_ORIGINS, cors_origins, create_app

WEBP = b"RIFF\x1a\x00\x00\x00WEBPVP8 fake"


@pytest.fixture
def media(tmp_path: Path) -> Path:
    (tmp_path / "abc.webp").write_bytes(WEBP)
    return tmp_path


def test_a_stored_image_is_served_with_its_type_and_cached(media):
    response = TestClient(create_app(media_dir=media)).get(MEDIA_PREFIX + "abc.webp")
    assert response.status_code == 200
    assert response.content == WEBP
    assert response.headers["content-type"] == "image/webp"
    assert response.headers["cache-control"] == "public, max-age=604800"


def test_a_missing_image_is_a_404_problem(media):
    response = TestClient(create_app(media_dir=media)).get("/media/nope.webp")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 404


@pytest.mark.parametrize("path", ["/media/..%2fsecret.txt", "/media/%2e%2e/secret.txt", "/media/../secret.txt"])
def test_files_outside_the_images_folder_are_never_served(media, path):
    (media.parent / "secret.txt").write_text("do not serve")
    response = TestClient(create_app(media_dir=media)).get(path)
    assert response.status_code == 404
    assert "do not serve" not in response.text


def test_the_api_starts_even_before_any_image_was_copied(tmp_path):
    client = TestClient(create_app(media_dir=tmp_path / "not-there-yet"))
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/media/abc.webp").status_code == 404


def test_the_scraper_runner_stores_images_where_the_api_serves_them():
    from app import run

    assert run.IMAGES_DIR == IMAGES_DIR


def test_an_allowed_origin_may_call_the_api_from_a_browser(media):
    client = TestClient(create_app(media_dir=media, origins=["http://localhost:8081"]))
    preflight = client.options(
        "/events", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "GET"}
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:8081"
    assert "GET" in preflight.headers["access-control-allow-methods"]
    assert "access-control-allow-credentials" not in preflight.headers
    response = client.get("/health", headers={"Origin": "http://localhost:8081"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_another_origin_gets_no_cors_permission(media):
    client = TestClient(create_app(media_dir=media, origins=["http://localhost:8081"]))
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_only_reading_is_allowed_across_origins(media):
    client = TestClient(create_app(media_dir=media, origins=["http://localhost:8081"]))
    preflight = client.options(
        "/events", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "DELETE"}
    )
    assert preflight.status_code == 400


def test_origins_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " https://recitar.example , https://www.recitar.example ,")
    assert cors_origins() == ["https://recitar.example", "https://www.recitar.example"]


def test_without_the_variable_only_the_local_expo_web_is_allowed(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert cors_origins() == DEFAULT_CORS_ORIGINS == ["http://localhost:8081", "http://127.0.0.1:8081"]
