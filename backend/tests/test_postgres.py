"""Tests that run against a real Postgres (see docker-compose.test.yml).

They are skipped unless TEST_DATABASE_URL is set. They WIPE that database, so
they refuse to run on one whose name does not contain "test".
"""

import os
from datetime import datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from app import current_user, db
from app.db import get_session, make_engine
from app.main import app
from app.models import Activity, User

TEST_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_URL, reason="set TEST_DATABASE_URL to run the Postgres tests"
)


@pytest.fixture
def migrated_url(monkeypatch):
    """An empty Postgres database with every migration applied."""
    if "test" not in (make_url(TEST_URL).database or ""):
        pytest.fail("refusing to wipe a database whose name does not contain 'test'")
    engine = make_engine(TEST_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    monkeypatch.setattr(db, "DATABASE_URL", TEST_URL)  # alembic/env.py reads this
    db.init_db()
    return TEST_URL


@pytest.fixture
def pg_session(migrated_url):
    engine = make_engine(migrated_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def add_user(session, auth_id="u-1", email="a@x.com", name="Amit") -> User:
    user = User(auth_id=auth_id, email=email, name=name)
    session.add(user)
    session.commit()
    return user


def make_activity(user_id, **fields) -> Activity:
    values = dict(
        user_id=user_id,
        source="fit",
        external_id="abc",
        sport="run",
        start_time_local=datetime(2026, 1, 1, 7, 0),
        duration_s=1800,
    )
    return Activity(**{**values, **fields})


def test_migrations_build_the_tables_and_match_the_models(migrated_url):
    engine = make_engine(migrated_url)
    assert set(inspect(engine).get_table_names()) == {
        "users",
        "activity",
        "alembic_version",
    }
    with engine.connect() as connection:
        differences = compare_metadata(
            MigrationContext.configure(connection), SQLModel.metadata
        )
    assert differences == []


def test_duplicate_email_rejected(pg_session):
    add_user(pg_session, auth_id="u-1", email="a@x.com")
    pg_session.add(User(auth_id="u-2", email="a@x.com", name="Other"))
    with pytest.raises(IntegrityError):
        pg_session.commit()


def test_duplicate_auth_id_rejected(pg_session):
    add_user(pg_session, auth_id="u-1", email="a@x.com")
    pg_session.add(User(auth_id="u-1", email="b@x.com", name="Other"))
    with pytest.raises(IntegrityError):
        pg_session.commit()


def test_same_workout_cannot_be_saved_twice(pg_session):
    user = add_user(pg_session)
    pg_session.add(make_activity(user.id))
    pg_session.commit()
    pg_session.add(make_activity(user.id))
    with pytest.raises(IntegrityError):
        pg_session.commit()


def test_activity_for_missing_user_rejected(pg_session):
    pg_session.add(make_activity(user_id=999))
    with pytest.raises(IntegrityError):
        pg_session.commit()


def test_activity_values_survive_a_round_trip(pg_session):
    user = add_user(pg_session)
    start = datetime(2026, 10, 12, 7, 1, 22)
    zones = [60.0, 120.5, 30.0, 10.0, 0.0]
    pg_session.add(make_activity(user.id, start_time_local=start, hr_zone_seconds=zones))
    pg_session.commit()
    pg_session.expire_all()

    saved = pg_session.exec(select(Activity)).one()
    assert saved.start_time_local == start
    assert saved.start_time_local.tzinfo is None
    assert saved.hr_zone_seconds == zones


@pytest.fixture
def pg_client(pg_session):
    app.dependency_overrides[get_session] = lambda: pg_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_first_login_race_recovers_on_postgres(pg_client, pg_session, bearer, monkeypatch):
    real_lookup = current_user.find_by_auth_id
    calls = []

    def miss_once(session, auth_id):
        calls.append(auth_id)
        return None if len(calls) == 1 else real_lookup(session, auth_id)

    monkeypatch.setattr(current_user, "find_by_auth_id", miss_once)
    add_user(pg_session, auth_id="u-1", email="a@x.com")

    response = pg_client.get("/users/me", headers=bearer("u-1", "a@x.com"))

    assert response.status_code == 200
    # Postgres poisons a transaction after a failed insert; this proves it was rolled back.
    assert len(pg_session.exec(select(User)).all()) == 1


def test_same_email_other_auth_id_is_409_on_postgres(pg_client, pg_session, bearer):
    add_user(pg_session, auth_id="old", email="a@x.com")

    response = pg_client.get("/users/me", headers=bearer("new", "a@x.com"))

    assert response.status_code == 409
    assert len(pg_session.exec(select(User)).all()) == 1
