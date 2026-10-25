from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.current_user import require_admin
from app.db import get_session
from app.main import app
from app.models import User


def tiny_app(session) -> TestClient:
    """A small app with one admin-only route, using the test database."""
    small = FastAPI()

    @small.get("/admin-only")
    def admin_only(user: User = Depends(require_admin)) -> dict:
        return {"email": user.email}

    small.dependency_overrides[get_session] = lambda: session
    return TestClient(small)


def test_ordinary_user_gets_403(session, bearer):
    response = tiny_app(session).get("/admin-only", headers=bearer())
    assert response.status_code == 403
    assert response.json()["detail"] == "Admins only"


def test_admin_gets_in(session, bearer, make_user):
    make_user(auth_id="u-1", email="a@x.com", is_admin=True)
    response = tiny_app(session).get("/admin-only", headers=bearer("u-1", "a@x.com"))
    assert response.status_code == 200
    assert response.json() == {"email": "a@x.com"}


def test_no_token_gets_401(session):
    assert tiny_app(session).get("/admin-only").status_code == 401


def body_fields(openapi_schema: dict) -> set[str]:
    """Every field name that any route accepts in a JSON request body."""
    fields = set()
    for operations in openapi_schema["paths"].values():
        for operation in operations.values():
            body = operation.get("requestBody", {})
            for content in body.get("content", {}).values():
                ref = content.get("schema", {}).get("$ref")
                if ref:
                    model = openapi_schema["components"]["schemas"][ref.split("/")[-1]]
                    fields |= set(model.get("properties", {}))
    return fields


def test_is_admin_cannot_be_set_through_the_api():
    assert "is_admin" not in body_fields(app.openapi())


def test_the_check_notices_a_route_that_accepts_is_admin():
    # Proves the test above can fail: a route that does take is_admin shows up.
    from sqlmodel import SQLModel

    class Sneaky(SQLModel):
        is_admin: bool

    small = FastAPI()

    @small.post("/sneaky")
    def sneaky(data: Sneaky) -> dict:
        return {}

    assert "is_admin" in body_fields(small.openapi())
