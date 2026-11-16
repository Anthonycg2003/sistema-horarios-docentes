"""Shared pytest fixtures for the backend test suite."""

import pytest
from sqlalchemy.orm import Session

from app.db.session import engine
from app.dependencies.db import get_db
from app.main import app


@pytest.fixture
def db_session():
    """Session bound to an outer transaction that is rolled back after the test.

    The same session is injected into the FastAPI app via dependency
    override, so the API sees what the test creates and everything is
    discarded at the end without touching the real database state.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()
