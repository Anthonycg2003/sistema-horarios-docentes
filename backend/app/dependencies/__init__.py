"""Shared FastAPI dependencies."""

from app.dependencies.db import get_db

__all__ = ["get_db"]