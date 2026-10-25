from datetime import datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from app import db
from app.db import connect_args_for
from app.models import Activity, User


def test_sqlite_needs_the_thread_flag():
    assert connect_args_for("sqlite:///./coach.db") == {"check_same_thread": False}


def test_other_databases_get_no_sqlite_flags():
    url = "postgresql+psycopg://user:pw@host:5432/postgres"
    assert connect_args_for(url) == {}


def test_activity_for_missing_user_is_rejected(session):
    session.add(
        Activity(
            user_id=999,
            source="fit",
            external_id="abc",
            sport="run",
            start_time_local=datetime(2026, 1, 1, 7, 0),
            duration_s=1800,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def make_activity(user_id, source="fit", external_id="abc"):
    return Activity(
        user_id=user_id,
        source=source,
        external_id=external_id,
        sport="run",
        start_time_local=datetime(2026, 1, 1, 7, 0),
        duration_s=1800,
    )


def test_same_workout_cannot_be_saved_twice(session, make_user):
    make_user()
    session.add(make_activity(user_id=1))
    session.commit()

    session.add(make_activity(user_id=1))  # same user, source and external_id
    with pytest.raises(IntegrityError):
        session.commit()


def test_same_external_id_is_fine_for_another_source_or_user(session, make_user):
    make_user()
    make_user(auth_id="u-2", email="d@x.com", name="Dana")
    session.add(make_activity(user_id=1))
    session.commit()

    session.add(make_activity(user_id=1, source="garmin"))  # other source
    session.add(make_activity(user_id=2))  # other user
    session.commit()  # no error: only the full combination must be unique


def test_two_users_cannot_share_an_auth_id(session, make_user):
    make_user(auth_id="u-1")

    session.add(User(auth_id="u-1", name="Other", email="o@x.com"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_table_is_called_users():
    # "user" is a reserved word in Postgres, so we avoid it as a table name.
    assert User.__tablename__ == "users"
    foreign_key = next(iter(Activity.__table__.c.user_id.foreign_keys))
    assert foreign_key.target_fullname == "users.id"


def test_init_db_runs_the_migrations(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    monkeypatch.setattr(db, "DATABASE_URL", url)  # alembic/env.py reads this

    db.init_db()

    tables = set(inspect(db.make_engine(url)).get_table_names())
    assert tables == {"users", "activity", "alembic_version"}


def test_migrations_match_the_models(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    monkeypatch.setattr(db, "DATABASE_URL", url)  # alembic/env.py reads this

    db.init_db()

    with db.make_engine(url).connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, SQLModel.metadata)
    # No differences means: if a model changed, its migration was written too.
    assert differences == []
