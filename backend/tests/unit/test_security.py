"""Unit tests for password hashing and JWT utilities."""

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_carries_subject_and_type() -> None:
    token = create_access_token("42")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_is_not_accepted_as_access() -> None:
    token = create_refresh_token("42")
    with pytest.raises(UnauthorizedError):
        decode_token(token, expected_type="access")


def test_expired_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import security

    monkeypatch.setattr(security.settings, "access_token_expire_minutes", -1)
    token = security.create_access_token("42")
    with pytest.raises(UnauthorizedError):
        security.decode_token(token, expected_type="access")


def test_password_longer_than_72_bytes_is_rejected() -> None:
    """A password over 72 bytes is rejected, not silently truncated."""
    long_password = "ñ" * 40  # 80 bytes in UTF-8
    with pytest.raises(ValueError):
        hash_password(long_password)
    assert not verify_password(long_password, hash_password("corto"))
