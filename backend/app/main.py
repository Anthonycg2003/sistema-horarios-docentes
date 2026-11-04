"""FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.middleware import RequestLoggingMiddleware
from app.core.redis import get_redis_client

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Sistema Horarios Docentes",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

register_error_handlers(app)
app.add_middleware(RequestLoggingMiddleware)

get_redis_client()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
