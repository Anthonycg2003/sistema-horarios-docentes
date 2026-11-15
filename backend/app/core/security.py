"""Password hashing and JWT creation/validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password.

    Passwords longer than 72 bytes are truncated by bcrypt itself; we do
    not pre-truncate to avoid silently changing the credential.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True when the plain password matches the stored hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    """Create a short-lived access token for the given subject."""
    return _create_token(
        subject,
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token for the given subject."""
    return _create_token(
        subject,
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode and validate a JWT, checking its type.

    Raises:
        UnauthorizedError: if the token is missing, malformed, expired,
            of the wrong type, or signed with a different key.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Token inválido") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError("Tipo de token incorrecto")
    if not payload.get("sub"):
        raise UnauthorizedError("Token inválido")
    return payload
