import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cors import add_cors, parse_origins
from app.db import init_db
from app.routes import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: bring the database up to date."""
    init_db()
    yield


app = FastAPI(title="Running Coach", lifespan=lifespan)
# Which web addresses may call us from a browser. Empty means nobody.
add_cors(app, parse_origins(os.environ.get("ALLOWED_ORIGINS", "")))
app.include_router(users.router)


@app.get("/health")
def health() -> dict:
    """Report that the API is up. Used to check the server is running."""
    return {"status": "ok"}
