import os
from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
# "jwks": Supabase signs with a key pair and publishes the public half.
# "hs256": an older shared secret, kept in SUPABASE_JWT_SECRET.
JWT_MODE = os.environ.get("JWT_MODE", "jwks")

ALGORITHMS = {"jwks": ["ES256", "RS256"], "hs256": ["HS256"]}


class InvalidToken(Exception):
    """The token is missing something, expired, forged, or for another project."""


@dataclass(frozen=True)
class TokenClaims:
    """The two facts we take from a valid token."""

    sub: str  # Supabase's id for this person
    email: str


@lru_cache
def _public_keys() -> PyJWKClient:
    """Fetches (and remembers) the project's public keys."""
    return PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")


def get_signing_key(token: str):
    """Return the key that must have signed this token. Tests replace this."""
    if JWT_MODE == "hs256":
        return os.environ["SUPABASE_JWT_SECRET"]
    return _public_keys().get_signing_key_from_jwt(token).key


def verify_token(token: str) -> TokenClaims:
    """Check a Supabase access token and return who it belongs to.

    Raises InvalidToken for any problem, so callers handle one error type.
    """
    try:
        claims = jwt.decode(
            token,
            get_signing_key(token),
            algorithms=ALGORITHMS[JWT_MODE],
            audience="authenticated",
            issuer=f"{SUPABASE_URL}/auth/v1",
            options={"require": ["exp", "aud", "iss", "sub"]},
        )
    except jwt.PyJWTError as error:
        raise InvalidToken(str(error)) from error

    sub, email = claims.get("sub"), claims.get("email")
    if not isinstance(sub, str) or not sub or not isinstance(email, str) or not email:
        raise InvalidToken("token has no user id or email")
    return TokenClaims(sub=sub, email=email)
