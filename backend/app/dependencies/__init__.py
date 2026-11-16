"""Shared FastAPI dependencies."""

from app.dependencies.auth import get_current_user, require_role
from app.dependencies.db import get_db

__all__ = ["get_current_user", "get_db", "require_role"]
