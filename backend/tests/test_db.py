from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import connect_args_for
from app.models import Activity


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
            start_time_local=datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc),
            duration_s=1800,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
