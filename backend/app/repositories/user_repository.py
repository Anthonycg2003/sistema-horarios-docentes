"""Database queries for the User model."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(db: Session, username: str) -> User | None:
    """Return the user with the given username, or None."""
    return db.scalar(select(User).where(User.username == username))


def get_by_id(db: Session, user_id: int) -> User | None:
    """Return the user with the given id, or None."""
    return db.get(User, user_id)
