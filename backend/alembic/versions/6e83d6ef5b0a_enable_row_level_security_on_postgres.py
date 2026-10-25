"""enable row level security on postgres

Supabase exposes every table in the public schema through a web API that
anyone holding the (public) anon key can call. With Row Level Security on and
no rules, outsiders see and change nothing. Our backend connects as the table
owner (postgres), and owners bypass these rules, so the backend is unaffected.

Revision ID: 6e83d6ef5b0a
Revises: a56a0ddaf265
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6e83d6ef5b0a'
down_revision: Union[str, Sequence[str], None] = 'a56a0ddaf265'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("users", "activity", "alembic_version")


def upgrade() -> None:
    """Lock outsiders out of every table. Postgres only: SQLite has no such feature."""
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Turn row level security off again."""
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
