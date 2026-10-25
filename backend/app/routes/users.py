from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict, Field, StringConstraints
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from app.db import get_session
from app.models import User

router = APIRouter()

# Strip spaces, and refuse an empty result.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Strip spaces, lowercase (so A@x.com and a@x.com are one person), and require
# the shape "something@something.something".
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class UserCreate(SQLModel):
    """The data a client sends to create a user."""

    # Fields we do not know (max_hr, is_admin, typos) get a 422 instead of being dropped.
    model_config = ConfigDict(extra="forbid")

    name: Name
    email: Email


class UserUpdate(SQLModel):
    """The data a client sends to change a user. For now, only max_hr."""

    model_config = ConfigDict(extra="forbid")

    # Beats per minute. null clears it. The range catches typos like 19 or 1900.
    max_hr: Annotated[int, Field(ge=100, le=250)] | None


@router.post("/users", status_code=201, response_model=User)
def create_user(data: UserCreate, session: Session = Depends(get_session)) -> User:
    """Create a user. Two users can't share an email."""
    user = User.model_validate(data)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # The database's unique rule on email caught a duplicate, even if
        # another request signed up with it a moment ago.
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already in use")
    session.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    """Return one user, or 404 if there is no such user."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=User)
def update_user(
    user_id: int, data: UserUpdate, session: Session = Depends(get_session)
) -> User:
    """Change a user's max heart rate, or 404 if there is no such user."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.max_hr = data.max_hr
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
