"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Sistena Horarios Docentes",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}