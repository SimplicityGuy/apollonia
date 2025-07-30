"""Shared pytest fixtures and configuration."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
from typing import Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import shared fixtures
from tests.fixtures import *  # noqa: F403, E402


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Configure test collection
def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:  # noqa: ARG001
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark slow tests
        if "test_docker" in item.nodeid or "test_large" in item.name:
            item.add_marker(pytest.mark.slow)

        # Skip Docker tests if Docker is not available
        if "docker" in item.keywords:
            import subprocess

            try:
                subprocess.run(["docker", "info"], capture_output=True, check=True)  # noqa: S607
            except (subprocess.CalledProcessError, FileNotFoundError):
                item.add_marker(pytest.mark.skip(reason="Docker not available"))


# Test environment configuration
@pytest.fixture(scope="session")
def test_env() -> dict[str, Any]:
    """Provide test environment configuration."""
    return {
        "rabbitmq_host": "localhost",
        "rabbitmq_port": 5672,
        "rabbitmq_user": "apollonia",
        "rabbitmq_password": "apollonia",
        "neo4j_host": "localhost",
        "neo4j_port": 7687,
        "neo4j_user": "neo4j",
        "neo4j_password": "apollonia",
        "test_data_dir": "/tmp/apollonia_test_data",  # noqa: S108
        "frontend_url": "http://localhost:3000",
        "api_url": "http://localhost:8000",
    }


# Logging configuration for tests
@pytest.fixture(autouse=True)
def configure_logging() -> None:
    """Configure logging for tests."""
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Reduce noise from third-party libraries
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Performance monitoring
@pytest.fixture
def benchmark_timer() -> Any:
    """Simple benchmark timer for performance testing."""
    import time

    class Timer:
        def __init__(self) -> None:
            self.times: dict[str, float] = {}

        def start(self, name: str) -> None:
            self.times[name] = time.time()

        def stop(self, name: str) -> float | None:
            if name in self.times:
                duration = time.time() - self.times[name]
                print(f"\n{name} took {duration:.3f} seconds")
                return duration
            return None

    return Timer()


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data(request: Any, test_env: dict[str, Any]) -> Generator[None, None, None]:  # noqa: ARG001
    """Ensure test data is cleaned up after tests."""
    yield

    # Cleanup test data directory if it exists
    import shutil

    test_data_path = Path(test_env["test_data_dir"])
    if test_data_path.exists():
        shutil.rmtree(test_data_path, ignore_errors=True)


# Test reporting
def pytest_report_header(config: Any) -> list[str]:  # noqa: ARG001
    """Add custom information to test report header."""
    import platform

    return [
        f"Platform: {platform.system()} {platform.release()}",
        f"Python: {platform.python_version()}",
        "Project: Apollonia Media Processing System",
    ]
