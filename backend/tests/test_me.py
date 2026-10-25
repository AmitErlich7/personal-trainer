import time

import pytest
from sqlmodel import select

from app import current_user
from app.models import User


def test_me_without_token_is_401(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not signed in"
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_garbage_token_is_401(client, bearer):
    response = client.get("/users/me", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_expired_token_is_401(client, bearer):
    headers = bearer(exp=int(time.time()) - 10)
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.parametrize("header", ["Bearer", "Bearer ", "Token abc", "abc"])
def test_malformed_authorization_headers_are_401(client, header):
    response = client.get("/users/me", headers={"Authorization": header})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not signed in"


def test_first_request_creates_the_user(client, bearer, session):
    response = client.get("/users/me", headers=bearer("u-1", "Amit@X.com"))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "amit@x.com"
    assert body["name"] == "amit"
    assert body["is_admin"] is False
    assert len(session.exec(select(User)).all()) == 1


def test_second_request_reuses_the_user(client, bearer, session):
    first = client.get("/users/me", headers=bearer()).json()
    second = client.get("/users/me", headers=bearer()).json()
    assert first["id"] == second["id"]
    assert len(session.exec(select(User)).all()) == 1


def test_each_user_sees_only_themselves(client, bearer):
    amit = client.get("/users/me", headers=bearer("u-1", "a@x.com")).json()
    dana = client.get("/users/me", headers=bearer("u-2", "d@x.com")).json()
    assert amit["email"] == "a@x.com"
    assert dana["email"] == "d@x.com"
    assert amit["id"] != dana["id"]


def test_simultaneous_first_logins_make_one_row(
    client, bearer, session, make_user, monkeypatch
):
    real_lookup = current_user.find_by_auth_id
    calls = []

    def miss_once(session, auth_id):
        # Pretend nobody exists yet, although another request just saved them.
        calls.append(auth_id)
        return None if len(calls) == 1 else real_lookup(session, auth_id)

    monkeypatch.setattr(current_user, "find_by_auth_id", miss_once)
    make_user(auth_id="u-1", email="a@x.com")

    response = client.get("/users/me", headers=bearer("u-1", "a@x.com"))

    assert response.status_code == 200
    assert len(session.exec(select(User)).all()) == 1


def test_same_email_other_auth_id_is_409(client, bearer, session, make_user):
    original = make_user(auth_id="old", email="a@x.com")

    response = client.get("/users/me", headers=bearer("new", "a@x.com"))

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already linked to another account"
    session.refresh(original)
    assert original.auth_id == "old"
    assert len(session.exec(select(User)).all()) == 1
