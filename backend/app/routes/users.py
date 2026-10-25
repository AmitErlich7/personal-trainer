from fastapi import APIRouter, Depends

from app.current_user import get_current_user
from app.models import User

router = APIRouter()


@router.get("/users/me", response_model=User)
def read_me(user: User = Depends(get_current_user)) -> User:
    """Return the signed-in user."""
    return user
