import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./coach.db")



def connect_args_for(url: str) -> dict:
    """Extra connection settings, only for databases that understand them."""
    if url.startswith("sqlite"):
        # SQLite refuses to share a connection between threads unless we say it's OK.
        return {"check_same_thread": False}
    return {}


engine = create_engine(DATABASE_URL, connect_args=connect_args_for(DATABASE_URL))


def init_db() -> None:
    """Create all tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Give one request its own database session, and close it afterwards."""
    with Session(engine) as session:
        yield session
