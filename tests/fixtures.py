"""Shared test fixtures and utilities for Apollonia tests."""

import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import orjson
import pytest
from aio_pika import Message
from neo4j import AsyncDriver

# --- File System Fixtures ---


@pytest.fixture
def temp_dir():
    """Create a temporary directory that's automatically cleaned up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_files(temp_dir):
    """Create a set of test files with various types."""
    files = {
        "text": temp_dir / "test.txt",
        "video": temp_dir / "video.mp4",
        "image": temp_dir / "image.jpg",
        "document": temp_dir / "document.pdf",
    }

    # Create files with content
    files["text"].write_text("Hello, World!")
    files["video"].write_bytes(b"fake video content")
    files["image"].write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header
    files["document"].write_bytes(b"%PDF-1.4")  # PDF header

    return files


@pytest.fixture
def neighbor_files(temp_dir):
    """Create a set of files with neighbor relationships."""
    main_file = temp_dir / "movie.mp4"
    neighbors = {
        "main": main_file,
        "subtitle": temp_dir / "movie.srt",
        "info": temp_dir / "movie.nfo",
        "thumbnail": temp_dir / "movie.jpg",
        "metadata": temp_dir / "movie.xml",
    }

    # Create all files
    for name, file_path in neighbors.items():
        file_path.write_text(f"Content for {name}")

    return neighbors


# --- Mock Data Factories ---


def create_file_metadata(
    file_path: str = "/test/file.txt",
    size: int = 1024,
    event_type: str = "IN_CREATE",
    neighbors: list[str] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create test file metadata."""
    timestamp = datetime.now(UTC).isoformat()

    data = {
        "file_path": file_path,
        "event_type": event_type,
        "sha256_hash": kwargs.get(
            "sha256_hash", "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        ),
        "xxh128_hash": kwargs.get("xxh128_hash", "4b2938d8f8e15d0e8c7c8e9a0b1c2d3e"),
        "size": size,
        "modified_time": kwargs.get("modified_time", timestamp),
        "accessed_time": kwargs.get("accessed_time", timestamp),
        "changed_time": kwargs.get("changed_time", timestamp),
        "timestamp": kwargs.get("timestamp", timestamp),
        "neighbors": neighbors or [],
    }

    return data


def create_amqp_message(data: dict[str, Any] | None = None) -> Message:
    """Create a mock AMQP message."""
    if data is None:
        data = create_file_metadata()

    message = Mock(spec=Message)
    message.body = orjson.dumps(data)
    message.delivery_tag = 1

    # Mock process context manager
    process_mock = AsyncMock()
    process_mock.__aenter__ = AsyncMock(return_value=None)
    process_mock.__aexit__ = AsyncMock(return_value=None)
    message.process.return_value = process_mock

    return message


# --- Service Mocks ---


@pytest.fixture
def mock_amqp_connection():
    """Create a mock AMQP connection with channel."""
    connection = AsyncMock()
    channel = AsyncMock()
    exchange = AsyncMock()
    queue = AsyncMock()

    # Set up the mock chain
    connection.channel.return_value = channel
    channel.declare_exchange.return_value = exchange
    channel.declare_queue.return_value = queue
    queue.bind = AsyncMock()

    # Mock message iterator
    async def empty_iterator():
        return
        yield  # Make it a generator

    queue.iterator.return_value.__aenter__.return_value.__aiter__ = empty_iterator

    return connection, channel, exchange, queue


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver with session."""
    driver = AsyncMock(spec=AsyncDriver)
    session = AsyncMock()
    result = AsyncMock()

    # Set up the mock chain
    driver.session.return_value.__aenter__.return_value = session
    driver.session.return_value.__aexit__.return_value = None
    session.run.return_value = result
    result.single.return_value = {"f": {"path": "/test/file.txt"}}
    result.value.return_value = 1  # For count queries

    # Mock async iteration for results
    async def mock_records():
        yield {"neighbor_path": "/test/neighbor1.txt"}
        yield {"neighbor_path": "/test/neighbor2.txt"}

    result.__aiter__ = mock_records

    return driver, session


# --- Test Data Sets ---


@pytest.fixture
def sample_file_dataset():
    """Provide a comprehensive dataset for testing."""
    return [
        {
            "file_path": "/media/movies/action/movie1.mp4",
            "size": 1073741824,  # 1GB
            "media_type": "video/mp4",
            "neighbors": ["/media/movies/action/movie1.srt", "/media/movies/action/movie1.nfo"],
        },
        {
            "file_path": "/media/music/album/track01.mp3",
            "size": 5242880,  # 5MB
            "media_type": "audio/mpeg",
            "neighbors": ["/media/music/album/cover.jpg", "/media/music/album/tracks.txt"],
        },
        {
            "file_path": "/documents/report.pdf",
            "size": 2097152,  # 2MB
            "media_type": "application/pdf",
            "neighbors": [],
        },
        {
            "file_path": "/images/photo.jpg",
            "size": 3145728,  # 3MB
            "media_type": "image/jpeg",
            "neighbors": ["/images/photo.raw", "/images/photo_thumb.jpg"],
        },
    ]


# --- Async Utilities ---


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def wait_for_condition(condition_func, timeout=5, interval=0.1):  # noqa: ASYNC109
    """Wait for a condition to become true."""
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)

    return False


# --- Platform-Specific Helpers ---


def skip_on_macos(func):
    """Decorator to skip tests on macOS."""
    import sys

    import pytest

    return pytest.mark.skipif(
        sys.platform == "darwin", reason="Test requires Linux-specific features"
    )(func)


def require_docker(func):
    """Decorator to skip tests if Docker is not available."""
    import subprocess

    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)  # noqa: S607
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_available = False

    return pytest.mark.skipif(not docker_available, reason="Test requires Docker")(func)


# --- Test User Data ---


@pytest.fixture
def test_users():
    """Provide test user data."""
    return [
        {
            "id": "1",
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
        },
        {
            "id": "2",
            "username": "user1",
            "email": "user1@example.com",
            "role": "user",
        },
        {
            "id": "3",
            "username": "viewer",
            "email": "viewer@example.com",
            "role": "viewer",
        },
    ]


# --- Performance Testing Helpers ---


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = asyncio.get_event_loop().time()
        self.duration = self.end_time - self.start_time
        print(f"{self.name} took {self.duration:.3f} seconds")

    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = asyncio.get_event_loop().time()
        self.duration = self.end_time - self.start_time
        print(f"{self.name} took {self.duration:.3f} seconds")


# --- Cleanup Utilities ---


@pytest.fixture
async def cleanup_neo4j(mock_neo4j_driver):
    """Fixture to clean up Neo4j test data."""
    driver, session = mock_neo4j_driver

    yield driver

    # Cleanup test nodes
    if hasattr(session, "run"):
        await session.run("MATCH (n:TestNode) DETACH DELETE n")


@pytest.fixture
def cleanup_files(temp_dir):  # noqa: ARG001
    """Fixture to track and clean up created files."""
    created_files = []

    def track_file(file_path):
        created_files.append(file_path)
        return file_path

    yield track_file

    # Cleanup
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()


# --- Mock Builders ---


class MockBuilder:
    """Builder for creating complex mock objects."""

    @staticmethod
    def amqp_message(**kwargs):
        """Build a mock AMQP message with custom data."""
        data = create_file_metadata(**kwargs)
        return create_amqp_message(data)

    @staticmethod
    def neo4j_result(records: list[dict[str, Any]]):
        """Build a mock Neo4j result with records."""
        result = AsyncMock()

        async def mock_iteration():
            for record in records:
                yield record

        result.__aiter__ = mock_iteration
        result.single.return_value = records[0] if records else None
        result.value.return_value = len(records)

        return result
