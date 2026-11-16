"""FastAPI dependencies that resolve the authenticated user and enforce roles."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.dependencies.db import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import user_repository


def _bearer_token(request: Request) -> str:
    """Extract the bearer token from the Authorization header."""
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("No autenticado")
    return token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Return the active user identified by the access token."""
    payload = decode_token(_bearer_token(request), expected_type=ACCESS_TOKEN_TYPE)
    user = user_repository.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("Sesión inválida")
    return user


def require_role(*roles: UserRole) -> Callable[..., User]:
    """Build a dependency that allows only the given roles."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError("No tiene permiso para esta operación")
        return user

    return _checker
