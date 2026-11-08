"""Alembic environment. Migrations run on the connection handed over by app.db.migrate, or on
DATABASE_URL when the `alembic` command is used directly."""

from alembic import context

from app.db import make_engine
from app.events_repository import metadata

connection = context.config.attributes.get("connection")
if connection is not None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    with make_engine().begin() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
