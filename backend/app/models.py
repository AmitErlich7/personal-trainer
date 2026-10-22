from pydantic import NaiveDatetime
from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """One person using the app."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    max_hr: int | None = None
    is_admin: bool = False


class Activity(SQLModel, table=True):
    """One workout (a run, a ride, a swim, ...)."""

    # The same workout can't be saved twice for the same user and source.
    __table_args__ = (UniqueConstraint("user_id", "source", "external_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    source: str  # "garmin" or "fit"
    external_id: str
    sport: str  # "run", "bike", "swim" or "other"
    name: str | None = None
    # The clock time where the workout happened, with no timezone on purpose.
    start_time_local: NaiveDatetime = Field(index=True)
    duration_s: float
    distance_m: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_power: float | None = None
    elevation_gain_m: float | None = None
    # Seconds spent in heart-rate zones Z1..Z5 (5 numbers), stored as JSON.
    hr_zone_seconds: list[float] | None = Field(default=None, sa_column=Column(JSON))
