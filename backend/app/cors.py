from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def parse_origins(raw: str) -> list[str]:
    """Turn "https://a.example, https://b.example/" into a clean list of origins.

    An origin has no path, so a trailing slash is removed (it would never match).
    """
    origins = (part.strip().rstrip("/") for part in raw.split(","))
    return [origin for origin in origins if origin]


def add_cors(app: FastAPI, origins: list[str]) -> None:
    """Let browser pages from exactly these origins call the API."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # never "*": that would mean any website
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,  # we send a token in a header, not cookies
    )
