import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api import events, venues
from app.api.problems import install_problem_handlers
from app.db import SERVER_DIR
from app.images.copy import IMAGES_DIR, MEDIA_PREFIX

# Expo's web dev server. Deployed clients are listed in CORS_ORIGINS instead.
DEFAULT_CORS_ORIGINS = ["http://localhost:8081", "http://127.0.0.1:8081"]
MEDIA_CACHE = "public, max-age=604800"  # a week: a stored image never changes under its name


def cors_origins() -> list[str]:
    """Browser origins allowed to call the API, from CORS_ORIGINS (comma-separated)."""
    raw = os.environ.get("CORS_ORIGINS")
    if raw is None:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class _CachedImages(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = MEDIA_CACHE
        return response


def create_app(media_dir: Path = IMAGES_DIR, origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="recitAR API")
    install_problem_handlers(app)
    app.include_router(events.router)
    app.include_router(venues.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # The folder is filled by the scraper runner; create it so a fresh checkout serves 404s, not 500s.
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount(MEDIA_PREFIX.rstrip("/"), _CachedImages(directory=media_dir), name="media")
    # Public, read-only API: only GET, no cookies or credentials.
    app.add_middleware(
        CORSMiddleware, allow_origins=cors_origins() if origins is None else origins, allow_methods=["GET"]
    )
    return app


load_dotenv(SERVER_DIR / ".env")
app = create_app()
