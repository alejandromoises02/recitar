"""Database connection (Postgres on Neon) and schema migrations.

The URL always comes from the environment, never from code. Use DATABASE_URL (direct) for
migrations and tests; DATABASE_URL_POOLED (through Neon's pooler) is for the running API.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

SERVER_DIR = Path(__file__).resolve().parent.parent


class MissingDatabaseError(RuntimeError):
    pass


def to_sqlalchemy_url(url: str) -> str:
    """Neon hands out `postgresql://`; SQLAlchemy needs the driver we installed (psycopg 3)."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def database_url(pooled: bool = False) -> str:
    load_dotenv(SERVER_DIR / ".env")
    name = "DATABASE_URL_POOLED" if pooled else "DATABASE_URL"
    url = (os.environ.get(name) or "").strip()
    if not url:
        raise MissingDatabaseError(f"Set {name} in server/.env (see server/README.md)")
    return to_sqlalchemy_url(url)


def make_engine(pooled: bool = False) -> Engine:
    return create_engine(database_url(pooled), pool_pre_ping=True)


def migrate(engine: Engine, revision: str = "head") -> None:
    """Bring the database behind `engine` to `revision` (default: the latest)."""
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, revision)
