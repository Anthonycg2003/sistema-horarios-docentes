"""Integration tests for /auth endpoints."""

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.models.enums import UserRole
from app.models.user import User


def _create_user(db, username: str = "ana", password: str = "secret", active: bool = True) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_returns_tokens_for_valid_credentials(db_session) -> None:
    _create_user(db_session)
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "ana", "password": "secret"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_fails_for_unknown_user(db_session) -> None:
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_login_fails_for_wrong_password(db_session) -> None:
    _create_user(db_session)
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "ana", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_login_fails_for_inactive_account(db_session) -> None:
    _create_user(db_session, active=False)
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "ana", "password": "secret"})
    assert response.status_code == 401


def test_me_requires_token(db_session) -> None:
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_identity_with_access_token(db_session) -> None:
    user = _create_user(db_session)
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "ana", "password": "secret"})
    token = login.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "ana"
    assert body["role"] == "administrador"
    assert body["is_active"] is True


def test_refresh_rejects_access_token(db_session) -> None:
    _create_user(db_session)
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "ana", "password": "secret"})
    access = login.json()["access_token"]

    response = client.post("/auth/refresh", json={"refresh_token": access})
    assert response.status_code == 401


def test_refresh_issues_new_pair(db_session) -> None:
    _create_user(db_session)
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "ana", "password": "secret"})
    refresh = login.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
