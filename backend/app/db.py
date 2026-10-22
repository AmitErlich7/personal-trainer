import os
from collections.abc import Iterator

from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./coach.db")


def connect_args_for(url: str) -> dict:
    """Extra connection settings, only for databases that understand them."""
    if url.startswith("sqlite"):
        # SQLite refuses to share a connection between threads unless we say it's OK.
        return {"check_same_thread": False}
    return {}


def make_engine(url: str, **kwargs) -> Engine:
    """Create a database engine. Used by the app and by the tests."""
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
    """Create all tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Give one request its own database session, and close it afterwards."""
    with Session(engine) as session:
        yield session
