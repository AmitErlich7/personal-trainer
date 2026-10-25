import time

import pytest

from app.auth import InvalidToken, TokenClaims, verify_token
from tests.auth_helpers import FORGER_KEY, make_token, use_test_signing


@pytest.fixture(autouse=True)
def trusted_signing(monkeypatch):
    use_test_signing(monkeypatch)


def test_valid_token_returns_claims():
    token = make_token("u-1", "a@x.com")
    assert verify_token(token) == TokenClaims("u-1", "a@x.com")


def test_expired_token_rejected():
    token = make_token(exp=int(time.time()) - 10)
    with pytest.raises(InvalidToken):
        verify_token(token)


def test_wrong_signature_rejected():
    token = make_token(key=FORGER_KEY)
    with pytest.raises(InvalidToken):
        verify_token(token)


def test_wrong_audience_rejected():
    with pytest.raises(InvalidToken):
        verify_token(make_token(aud="someone-else"))


def test_wrong_issuer_rejected():
    with pytest.raises(InvalidToken):
        verify_token(make_token(iss="https://other-project.supabase.co/auth/v1"))


def test_token_without_email_rejected():
    with pytest.raises(InvalidToken):
        verify_token(make_token(email=None))


def test_token_without_sub_rejected():
    with pytest.raises(InvalidToken):
        verify_token(make_token(sub=None))


def test_token_without_expiry_rejected():
    with pytest.raises(InvalidToken):
        verify_token(make_token(exp=None))


def test_garbage_string_rejected():
    with pytest.raises(InvalidToken):
        verify_token("not-a-token")
