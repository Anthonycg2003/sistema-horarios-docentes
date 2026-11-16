"""Request and response schemas for authentication."""

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """Credentials sent to POST /auth/login."""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def _password_within_bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar los 72 bytes en UTF-8")
        return value


class RefreshRequest(BaseModel):
    """Refresh token sent to POST /auth/refresh."""

    refresh_token: str = Field(min_length=1)


class TokenPair(BaseModel):
    """Access and refresh tokens returned after a successful login or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Authenticated user's identity, returned by GET /auth/me."""

    id: int
    username: str
    role: UserRole
    display_name: str
    is_active: bool
