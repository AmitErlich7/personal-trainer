"""Helpers that make fake Supabase tokens for tests. Nothing here talks to the network."""

import time

import jwt
from cryptography.hazmat.primitives.asymmetric import ec

from app import auth

TEST_SUPABASE_URL = "https://test-project.supabase.co"

# Two throwaway key pairs. Tokens signed with the first one are "real" in tests;
# tokens signed with the second one stand in for a forger.
SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
FORGER_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(sub="u-1", email="a@x.com", *, key=SIGNING_KEY, **overrides) -> str:
    """Build a signed token. Pass a claim as None to leave it out."""
    claims = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "iss": f"{TEST_SUPABASE_URL}/auth/v1",
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    claims = {name: value for name, value in claims.items() if value is not None}
    return jwt.encode(claims, key, algorithm="ES256")


def use_test_signing(monkeypatch) -> None:
    """Make the app trust tokens signed by SIGNING_KEY for TEST_SUPABASE_URL."""
    monkeypatch.setattr(auth, "SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setattr(auth, "get_signing_key", lambda token: SIGNING_KEY.public_key())
