from fastapi import FastAPI

app = FastAPI(title="Running Coach")


@app.get("/health")
def health() -> dict:
    """Report that the API is up. Used to check the server is running."""
    return {"status": "ok"}
