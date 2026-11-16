"""Authentication endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Verify credentials and return a new access/refresh pair."""
    user = auth_service.authenticate(db, payload.username, payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Exchange a valid refresh token for a new access/refresh pair."""
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    """Return the identity of the authenticated user."""
    return auth_service.to_user_read(db, user)
