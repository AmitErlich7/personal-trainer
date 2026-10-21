from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routes import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: make sure the tables exist."""
    init_db()
    yield


app = FastAPI(title="Running Coach", lifespan=lifespan)
app.include_router(users.router)


@app.get("/health")
def health() -> dict:
    """Report that the API is up. Used to check the server is running."""
    return {"status": "ok"}
