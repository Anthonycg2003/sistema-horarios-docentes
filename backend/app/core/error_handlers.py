"""Global exception handlers for the FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    """Convert a domain exception into a JSON error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register handlers for domain exceptions on the application."""
    app.add_exception_handler(DomainError, domain_error_handler)
