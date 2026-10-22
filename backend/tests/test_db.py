from app.db import connect_args_for


def test_sqlite_needs_the_thread_flag():
    assert connect_args_for("sqlite:///./coach.db") == {"check_same_thread": False}


def test_other_databases_get_no_sqlite_flags():
    url = "postgresql+psycopg://user:pw@host:5432/postgres"
    assert connect_args_for(url) == {}

