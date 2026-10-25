from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import User

router = APIRouter()


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    """Return one user, or 404 if there is no such user."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
