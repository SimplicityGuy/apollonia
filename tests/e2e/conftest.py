"""Configuration for end-to-end tests."""

import os
import subprocess
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="session")
def frontend_server() -> Generator[str, None, None]:
    """Start the frontend development server for testing."""
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"

    # Check if we should start the server
    if os.getenv("E2E_SKIP_SERVER_START"):
        yield "http://localhost:3000"
        return

    # Start frontend server
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    for _i in range(max_retries):
        try:
            import requests

            response = requests.get("http://localhost:3000", timeout=1)
            if response.status_code == 200:
                break
        except Exception:  # noqa: S110
            pass
        time.sleep(1)
    else:
        process.terminate()
        pytest.fail("Frontend server failed to start")

    yield "http://localhost:3000"

    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """Start the backend API server for testing."""
    backend_dir = Path(__file__).parent.parent.parent

    # Check if we should start the server
    if os.getenv("E2E_SKIP_SERVER_START"):
        yield "http://localhost:8000"
        return

    # Start backend server
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "api.main:app", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    for _i in range(max_retries):
        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                break
        except Exception:  # noqa: S110
            pass
        time.sleep(1)
    else:
        process.terminate()
        pytest.fail("Backend server failed to start")

    yield "http://localhost:8000"

    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """Configure browser context for testing."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="function")
def authenticated_page(page: Any, backend_server: str) -> Any:  # noqa: ARG001
    """Provide a page with authenticated user."""
    # Mock authentication
    page.route(
        "**/api/auth/login",
        lambda route: route.fulfill(
            status=200,
            json={
                "token": "fake-jwt-token",
                "user": {"id": "1", "username": "testuser", "email": "test@example.com"},
            },
        ),
    )

    # Set auth token in local storage
    page.goto("http://localhost:3000")
    page.evaluate("""
        localStorage.setItem('auth-token', 'fake-jwt-token');
        localStorage.setItem('user', JSON.stringify({
            id: '1',
            username: 'testuser',
            email: 'test@example.com'
        }));
    """)

    # Add auth header to all API requests
    page.route(
        "**/api/**",
        lambda route: route.continue_(
            headers={**route.request.headers, "Authorization": "Bearer fake-jwt-token"}
        ),
    )

    return page


@pytest.fixture(scope="session")
def test_data() -> dict[str, Any]:
    """Provide test data for e2e tests."""
    return {
        "users": [{"username": "testuser", "password": "testpass123", "email": "test@example.com"}],
        "files": [
            {
                "id": "1",
                "filename": "test_video.mp4",
                "media_type": "video/mp4",
                "file_size": 10485760,  # 10MB
                "processing_status": "completed",
                "sha256_hash": "abc123",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "filename": "test_image.jpg",
                "media_type": "image/jpeg",
                "file_size": 2097152,  # 2MB
                "processing_status": "processing",
                "sha256_hash": "def456",
                "created_at": "2024-01-02T00:00:00Z",
            },
        ],
        "catalogs": [
            {"id": "1", "name": "Test Catalog", "description": "A test catalog", "item_count": 10}
        ],
    }


@pytest.fixture
def mock_api_responses(page: Any, test_data: dict[str, Any]) -> Any:
    """Mock common API responses."""
    # Mock file listing
    page.route(
        "**/api/media/files*",
        lambda route: route.fulfill(
            status=200,
            json={
                "items": test_data["files"],
                "total": len(test_data["files"]),
                "page": 1,
                "page_size": 10,
            },
        ),
    )

    # Mock catalog listing
    page.route(
        "**/api/catalogs*",
        lambda route: route.fulfill(
            status=200, json={"items": test_data["catalogs"], "total": len(test_data["catalogs"])}
        ),
    )

    # Mock health check
    page.route("**/api/health", lambda route: route.fulfill(status=200, json={"status": "healthy"}))

    return page


# Playwright pytest plugin configuration
def pytest_configure(config: Any) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "authenticated: mark test as requiring authentication")
