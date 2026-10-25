from datetime import datetime

from sqlmodel import select

from app.models import Activity, User


def test_activity_keeps_naive_local_start_time(session, make_user):
    user = make_user()
    start = datetime(2026, 10, 12, 7, 1, 22)  # 07:01 on the watch's clock

    session.add(
        Activity(
            user_id=user.id,
            source="fit",
            external_id="1",
            sport="run",
            start_time_local=start,
            duration_s=1800,
        )
    )
    session.commit()
    session.expire_all()  # forget what we just saved, so we read it back from the DB

    saved = session.exec(select(Activity)).one()
    assert saved.start_time_local == start
    assert saved.start_time_local.tzinfo is None
