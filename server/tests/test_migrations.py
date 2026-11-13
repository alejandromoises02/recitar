from datetime import datetime, timezone

from sqlalchemy import text

from app.db import migrate


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
