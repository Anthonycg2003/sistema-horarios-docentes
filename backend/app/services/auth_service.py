"""Authentication logic: credential verification and token issuing."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.academic_program import Coordinator, DepartmentHead, Student
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import TokenPair, UserRead

INVALID_CREDENTIALS = "Credenciales inválidas"


def authenticate(db: Session, username: str, password: str) -> User:
    """Verify credentials and return the active user.

    The error message is the same whether the username does not exist or
    the password is wrong, so the response does not reveal which one
    failed (issue #40).
    """
    user = user_repository.get_by_username(db, username)
    if user is None:
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not user.is_active:
        raise UnauthorizedError(INVALID_CREDENTIALS)
    return user


def issue_tokens(user: User) -> TokenPair:
    """Build a new access/refresh pair for the given user."""
    subject = str(user.id)
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def refresh_tokens(db: Session, refresh_token: str) -> TokenPair:
    """Validate a refresh token and issue a new pair.

    The refresh token is checked for its type and the user is reloaded
    from the database so a deactivated account cannot keep its session
    alive.
    """
    payload = decode_token(refresh_token, expected_type="refresh")
    user = user_repository.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("Sesión inválida")
    return issue_tokens(user)


def _display_name(db: Session, user: User) -> str:
    """Derive the display name from the domain profile linked to the account."""
    if user.role == UserRole.COORDINATOR and user.coordinator_id is not None:
        profile = db.get(Coordinator, user.coordinator_id)
    elif user.role == UserRole.DEPARTMENT_HEAD and user.department_head_id is not None:
        profile = db.get(DepartmentHead, user.department_head_id)
    elif user.role == UserRole.STUDENT and user.student_id is not None:
        profile = db.get(Student, user.student_id)
    else:
        profile = None
    return profile.name if profile is not None else user.username


def to_user_read(db: Session, user: User) -> UserRead:
    """Build the public representation of an authenticated user."""
    return UserRead(
        id=user.id,
        username=user.username,
        role=user.role,
        display_name=_display_name(db, user),
        is_active=user.is_active,
    )
