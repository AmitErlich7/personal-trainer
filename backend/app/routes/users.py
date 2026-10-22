from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from app.db import get_session
from app.models import User

router = APIRouter()


class UserCreate(SQLModel):
    """The data a client sends to create a user."""

    name: str
    email: str


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
