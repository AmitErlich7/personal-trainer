import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from app import models  # noqa: F401  (importing it registers the tables)
from app.db import get_session, make_engine
from app.main import app
from app.models import User


@pytest.fixture
def session():
    """A fresh, empty in-memory database for one test."""
    engine = make_engine("sqlite://", poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    """A TestClient whose API uses the test database instead of the real one."""
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(session):
    """A function that saves a user and returns it. Override any field you need."""

    def make(auth_id="u-1", email="a@x.com", name="Amit", **fields) -> User:
        user = User(auth_id=auth_id, email=email, name=name, **fields)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return make
