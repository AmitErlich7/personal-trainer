from datetime import datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

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
