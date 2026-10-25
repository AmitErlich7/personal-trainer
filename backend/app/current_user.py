from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth import InvalidToken, verify_token
from app.db import get_session
from app.models import User

# auto_error=False: a missing header gives us None, so we choose the 401 message.
bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    """A 401 answer. The header tells clients which kind of login we expect."""
    return HTTPException(
        status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def find_by_auth_id(session: Session, auth_id: str) -> User | None:
    """Return the user with this Supabase id, or None."""
    return session.exec(select(User).where(User.auth_id == auth_id)).first()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Return the signed-in user, creating their row on the first sign-in."""
    if credentials is None:
        raise unauthorized("Not signed in")
    try:
        claims = verify_token(credentials.credentials)
    except InvalidToken:
        raise unauthorized("Invalid or expired token")

    user = find_by_auth_id(session, claims.sub)
    if user is not None:
        return user

    email = claims.email.lower()
    user = User(auth_id=claims.sub, email=email, name=email.split("@")[0])
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # Another request may have just created this same person. If so, use theirs.
        existing = find_by_auth_id(session, claims.sub)
        if existing is not None:
            return existing
        # Otherwise this email belongs to a different account.
        raise HTTPException(
            status_code=409, detail="Email already linked to another account"
        )
    session.refresh(user)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Return the signed-in user, but only if they are an admin."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return user
