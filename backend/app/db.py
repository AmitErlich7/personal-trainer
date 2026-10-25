import os
from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, event
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./coach.db")


def normalize_url(url: str) -> str:
    """Make a database URL ready for SQLAlchemy.

    Supabase gives "postgresql://...", which SQLAlchemy would hand to an older
    driver we don't use, so we name psycopg. A remote Postgres also gets
    sslmode=require unless the URL already says otherwise, so the password and
    data are never sent unencrypted by accident.
    """
    parsed = make_url(url)
    if parsed.drivername not in ("postgresql", "postgres"):
        return url
    parsed = parsed.set(drivername="postgresql+psycopg")
    is_local = parsed.host in (None, "localhost", "127.0.0.1", "::1")
    if not is_local and "sslmode" not in parsed.query:
        parsed = parsed.update_query_dict({"sslmode": "require"})
    return parsed.render_as_string(hide_password=False)


def connect_args_for(url: str) -> dict:
    """Extra connection settings, only for databases that understand them."""
    if url.startswith("sqlite"):
        # SQLite refuses to share a connection between threads unless we say it's OK.
        return {"check_same_thread": False}
    return {}


def make_engine(url: str, **kwargs) -> Engine:
    """Create a database engine. Used by the app and by the tests."""
    url = normalize_url(url)
    if not url.startswith("sqlite"):
        # Cloud databases drop idle connections; test each one before reusing it.
        kwargs.setdefault("pool_pre_ping", True)
    engine = create_engine(url, connect_args=connect_args_for(url), **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def turn_on_foreign_keys(dbapi_connection, _record):
            # SQLite ignores foreign keys unless asked, on every new connection.
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = make_engine(DATABASE_URL)


def init_db() -> None:
    """Bring the database up to date by running every migration not yet applied."""
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


def get_session() -> Iterator[Session]:
    """Give one request its own database session, and close it afterwards."""
    with Session(engine) as session:
        yield session
