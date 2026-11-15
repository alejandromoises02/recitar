from datetime import datetime, timezone

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.db import SERVER_DIR, migrate


def test_events_stored_before_first_seen_existed_get_the_migration_time(unmigrated_db_engine):
    migrate(unmigrated_db_engine, "0002")
    with unmigrated_db_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO events (id, category, title, venue, starts_at, ticket_links, source_url, updated_at) "
            "VALUES ('venti-a-20261120T2100', 'concert', 'A', 'Niceto Club', now(), '[]', 'https://x', now())"
        ))
    before = datetime.now(timezone.utc)
    migrate(unmigrated_db_engine)
    with unmigrated_db_engine.connect() as conn:
        first_seen, now = conn.execute(text("SELECT first_seen_at, now() FROM events")).one()
        default = conn.execute(text(
            "SELECT column_default FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'events' AND column_name = 'first_seen_at'"
        )).scalar_one()
    # Same clock as the database, so no drift between this machine and Neon matters.
    assert first_seen <= now
    assert (now - first_seen).total_seconds() < 300 + (datetime.now(timezone.utc) - before).total_seconds()
    assert default is None  # the app always writes it; no silent default for new rows


def test_events_stored_before_time_known_existed_keep_their_time_as_known(unmigrated_db_engine):
    migrate(unmigrated_db_engine, "0004")
    with unmigrated_db_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO events (id, category, title, venue, starts_at, ticket_links, source_url, updated_at, first_seen_at) "
            "VALUES ('venti-a-20261120T2100', 'concert', 'A', 'Niceto Club', now(), '[]', 'https://x', now(), now())"
        ))
    migrate(unmigrated_db_engine)
    with unmigrated_db_engine.connect() as conn:
        assert conn.execute(text("SELECT time_known FROM events")).scalar_one() is True
        nullable, default = conn.execute(text(
            "SELECT is_nullable, column_default FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'events' AND column_name = 'time_known'"
        )).one()
    assert nullable == "NO"
    assert default is None  # the app always writes it; no silent default for new rows


def test_ticket_clicks_are_counted_apart_from_the_events_and_the_migration_can_be_undone(unmigrated_db_engine):
    from sqlalchemy import inspect

    migrate(unmigrated_db_engine)
    columns = {c["name"]: c for c in inspect(unmigrated_db_engine).get_columns("ticket_clicks")}
    assert set(columns) == {"id", "show_key", "event_id", "vendor", "source", "created_at"}
    assert [name for name, c in columns.items() if c["nullable"]] == ["vendor"]
    assert inspect(unmigrated_db_engine).get_foreign_keys("ticket_clicks") == []  # the count outlives the event rows
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "migrations"))
    with unmigrated_db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0005")
    assert "ticket_clicks" not in inspect(unmigrated_db_engine).get_table_names()
