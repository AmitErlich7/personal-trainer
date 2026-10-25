from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from app.cors import add_cors, parse_origins
from app.main import app

ALLOWED = "https://friends.example"


def client_allowing(origins: list[str]) -> TestClient:
    """A tiny app with one route and the CORS rules under test."""
    small = FastAPI()

    @small.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    add_cors(small, origins)
    return TestClient(small)


def preflight(client: TestClient, origin: str):
    """The OPTIONS question a browser asks before a GET with an Authorization header."""
    return client.options(
        "/ping",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_allowed_origin_gets_its_own_address_back():
    response = preflight(client_allowing([ALLOWED]), ALLOWED)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_other_origin_is_refused():
    response = preflight(client_allowing([ALLOWED]), "https://evil.example")
    assert "access-control-allow-origin" not in response.headers


def test_nobody_is_allowed_when_no_origins_are_set():
    response = preflight(client_allowing([]), ALLOWED)
    assert "access-control-allow-origin" not in response.headers


def test_cookies_are_not_allowed():
    response = preflight(client_allowing([ALLOWED]), ALLOWED)
    assert "access-control-allow-credentials" not in response.headers


def test_parse_origins_trims_spaces_blanks_and_trailing_slashes():
    raw = " https://a.example/ , ,https://b.example,"
    assert parse_origins(raw) == ["https://a.example", "https://b.example"]


def test_parse_origins_of_nothing_is_empty():
    assert parse_origins("") == []


def test_the_real_app_uses_the_cors_middleware():
    assert any(m.cls is CORSMiddleware for m in app.user_middleware)
