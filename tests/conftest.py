"""
Pytest configuration and shared fixtures for test suite.

This module provides pytest configuration and fixtures that are shared
across all test modules. It handles database setup, teardown, and
test isolation to ensure tests run independently and reliably.
"""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import close_db, get_db_context, init_db
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Initialize the test database before running tests.

    This fixture runs once per test session and:
    1. Sets up a test database URL (if not already set)
    2. Initializes database tables using SQLAlchemy models
    3. Cleans up database connections after all tests complete

    The autouse=True parameter means this fixture runs automatically
    for all tests without needing to be explicitly requested.
    """
    # Ensure we're using a test database
    if "test" not in os.getenv("DATABASE_URL", ""):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_frames.db"

    # Initialize database tables
    await init_db()

    yield

    # Cleanup after all tests
    await close_db()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for individual tests.

    Each test gets a fresh session that is rolled back after the test
    completes, ensuring test isolation.

    Usage:
        async def test_something(db_session):
            # Use db_session here
            result = await db_session.execute(...)
    """
    async with get_db_context() as session:
        yield session


@pytest.fixture(scope="module")
def client():
    """
    Provide a FastAPI test client for API tests.

    This client can be used to make HTTP requests to the API endpoints
    during testing. It automatically handles the application lifespan
    events (startup/shutdown).

    Usage:
        def test_endpoint(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    with TestClient(app) as test_client:
        yield test_client
