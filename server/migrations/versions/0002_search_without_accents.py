"""Accent- and case-insensitive search support.

`unaccent` is a standard Postgres extension (available on Neon). It goes into `public`, and
`f_unaccent` wraps it as IMMUTABLE with the dictionary named explicitly, so it works whatever the
search_path is (tests run in their own schema) and an index can use it later if needed.

Revision ID: 0002
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA public")
    op.execute(
        "CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text "
        "LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT "
        "RETURN public.unaccent('public.unaccent'::regdictionary, $1)"
    )


def downgrade() -> None:
    # The extension stays: it is database-wide and harmless; other schemas may use it.
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
