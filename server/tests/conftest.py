"""Database tests are opt-in: they talk to a real Postgres (the Neon `dev` branch).

Run them with `RUN_DB_TESTS=1 python -m pytest`; the URL comes from server/.env. Each test run
works in its own throw-away schema, which is dropped at the end, so no real data is touched.
"""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.db import migrate, to_sqlalchemy_url
from app.main import app

RUN_DB_TESTS = os.environ.get("RUN_DB_TESTS") == "1"
if RUN_DB_TESTS:
    load_dotenv(Path(__file__).parent.parent / ".env")


@pytest.fixture
def db_engine(unmigrated_db_engine):
    migrate(unmigrated_db_engine)
    return unmigrated_db_engine


@pytest.fixture
def unmigrated_db_engine():
    """An empty throw-away schema, for tests that run the migrations themselves."""
    url = os.environ.get("DATABASE_URL")
    if not RUN_DB_TESTS or not url:
        pytest.skip("set RUN_DB_TESTS=1 (and DATABASE_URL in server/.env) to run the database tests")
    schema = f"test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(to_sqlalchemy_url(url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    # The pooled URL does not accept startup options, so tests always use the direct one.
    engine = create_engine(to_sqlalchemy_url(url), connect_args={"options": f"-csearch_path={schema}"})
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """The shared app keeps its counts in memory; every test starts with none."""
    for limiter in app.state.rate_limits.values():
        limiter.reset()
    yield
