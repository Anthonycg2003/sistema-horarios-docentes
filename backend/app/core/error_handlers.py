"""Global exception handlers for the FastAPI application."""
import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import DomainError

logger = logging.getLogger(__name__)


def _with_bearer_on_401(
    status_code: int, headers: Mapping[str, str] | None
) -> Mapping[str, str] | None:
    """Return headers adding WWW-Authenticate: Bearer when the status is 401."""
    if status_code != 401:
        return headers
    merged = dict(headers) if headers else {}
    merged.setdefault("WWW-Authenticate", "Bearer")
    return merged


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    """Return the domain error with its status and a uniform body.

    A 401 response carries the WWW-Authenticate: Bearer header.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=_with_bearer_on_401(exc.status_code, None),
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a 422 response with a readable detail for invalid request bodies."""
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(part) for part in first.get("loc", []))
        msg = first.get("msg", "Invalid value")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Invalid request data"
    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )


async def integrity_error_handler(
    _request: Request, exc: IntegrityError
) -> JSONResponse:
    """Return a 409 response for a data integrity conflict.

    SQL details are logged server-side but never exposed to the client.
    """
    logger.error("Database integrity error", exc_info=exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflict: data integrity violation"},
    )


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Return an HTTPException with a uniform body.

    Preserves the original status code. 401 responses carry the
    WWW-Authenticate: Bearer header.
    """
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=_with_bearer_on_401(exc.status_code, exc.headers),
    )


async def unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Return a generic 500 response for an unexpected error.

    The exception is logged server-side; no trace or internal detail reaches
    the client.
    """
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register the global exception handlers on the application."""
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
