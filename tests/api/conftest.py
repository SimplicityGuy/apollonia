"""API test configuration and fixtures."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.config import Settings, get_settings
from api.database import get_session
from api.main import app
from api.utils.cache import get_cache
from database.models import Base


# Override settings for testing
def get_test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379",
        cors_origins=["*"],
        debug=True,
        secret_key="test-secret-key",  # noqa: S106
        environment="test",
    )


# Override the settings dependency
app.dependency_overrides[get_settings] = get_test_settings


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
async def mock_db_session():
    """Mock async database session."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.scalar = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.run_sync = AsyncMock()

    # Mock for health check
    mock_session.execute.return_value.scalar.return_value = 1

    return mock_session


@pytest.fixture(scope="function")
async def mock_redis_client():
    """Mock Redis client."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.incr = AsyncMock(return_value=1)
    mock_client.ttl = AsyncMock(return_value=3600)
    mock_client.close = AsyncMock()

    return mock_client


@pytest.fixture(scope="function")
async def mock_neo4j_session():
    """Mock Neo4j session for tests expecting Neo4j."""
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()
    mock_session.close = AsyncMock()

    # Setup default mock responses
    mock_result = MagicMock()
    mock_result.single = MagicMock(return_value=None)
    mock_result.data = MagicMock(return_value=[])
    mock_session.run.return_value = mock_result

    return mock_session


@pytest.fixture(autouse=True)
async def setup_test_dependencies(mock_db_session, mock_redis_client, mock_neo4j_session):
    """Setup test dependencies for all tests."""

    # Mock database session
    async def mock_get_session():
        yield mock_db_session

    # Mock Redis client
    async def mock_get_cache():
        return mock_redis_client

    # Mock Neo4j session (for tests expecting Neo4j)
    async def mock_get_neo4j_session():
        yield mock_neo4j_session

    # Override dependencies
    app.dependency_overrides[get_session] = mock_get_session
    app.dependency_overrides[get_cache] = mock_get_cache

    # Add Neo4j compatibility
    from api import database

    if not hasattr(database, "get_neo4j_session"):
        database.get_neo4j_session = mock_get_neo4j_session

    # Mock the global objects to prevent initialization errors
    with (
        patch("api.database.async_session_factory", AsyncMock()),
        patch("api.utils.cache.redis_client", mock_redis_client),
        patch("api.database.get_neo4j_session", mock_get_neo4j_session),
    ):
        yield

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Create an authenticated test client."""
    # Mock authentication for protected endpoints
    from api.endpoints.auth import User, get_current_active_user

    mock_user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False,
        hashed_password="$2b$12$test",  # noqa: S106
    )

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_active_user] = mock_get_current_user

    return client


# Environment variable setup for tests
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"
