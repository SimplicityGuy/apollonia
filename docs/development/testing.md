# Testing Guide

Comprehensive testing strategy for the Apollonia media catalog system, covering unit tests,
integration tests, and end-to-end testing.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Testing Best Practices](#testing-best-practices)
- [Continuous Integration](#continuous-integration)

## Testing Philosophy

Apollonia follows a comprehensive testing strategy based on the testing pyramid:

```
    /\
   /  \     E2E Tests (Few)
  /____\    - User workflows
 /      \   - System integration
/__________\ - Critical path testing

/          \
\__________/ Integration Tests (Some)
/          \ - Service interactions
\__________/ - Database operations
             - Message queue flows

/____________\
\____________/ Unit Tests (Many)
/____________\ - Business logic
\____________/ - Utility functions
               - Component behavior
```

### Testing Principles

1. **Test Pyramid**: Majority unit tests, some integration tests, few E2E tests
1. **Fast Feedback**: Unit tests run in \<10 seconds, integration in \<2 minutes
1. **Isolation**: Tests don't depend on external services or shared state
1. **Deterministic**: Tests produce consistent results across environments
1. **Maintainable**: Tests are easy to read, write, and maintain

## Test Structure

### Directory Layout

```
tests/
├── unit/                    # Unit tests
│   ├── test_ingestor.py    # Ingestor service tests
│   ├── test_populator.py   # Populator service tests
│   ├── test_analyzer.py    # ML Analyzer tests
│   ├── test_api.py         # API service tests
│   └── test_shared.py      # Shared utilities tests
├── integration/             # Integration tests
│   ├── test_amqp_flow.py   # Message queue integration
│   ├── test_database.py    # Database operations
│   ├── test_file_flow.py   # File processing pipeline
│   └── test_api_services.py # API service integration
├── e2e/                     # End-to-end tests
│   ├── test_full_workflow.py # Complete user workflows
│   ├── test_web_interface.py # Frontend functionality
│   └── test_api_endpoints.py # API endpoint testing
├── performance/             # Performance tests
│   ├── test_load.py        # Load testing
│   ├── test_stress.py      # Stress testing
│   └── test_benchmarks.py  # Performance benchmarks
├── fixtures/                # Test data and fixtures
│   ├── media/              # Sample media files
│   ├── config/             # Test configurations
│   └── data/               # Test datasets
└── conftest.py             # Pytest configuration
```

## Running Tests

### Using Just (Recommended)

```bash
# Run all tests
just test

# Run specific test types
just test-unit           # Unit tests only
just test-integration    # Integration tests only
just test-e2e           # End-to-end tests only
just test-performance   # Performance tests only

# Run with coverage
just test-coverage

# Run tests in watch mode
just test-watch

# Run specific test file
just test tests/unit/test_ingestor.py

# Run with specific markers
just test -m "slow"      # Run only slow tests
just test -m "not slow"  # Skip slow tests
```

### Using pytest Directly

```bash
# Install test dependencies
uv sync --group test

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific tests
uv run pytest tests/unit/test_ingestor.py -v

# Run with specific markers
uv run pytest -m "integration" -v

# Run in parallel
uv run pytest -n auto
```

### Test Environment Setup

```bash
# Set up test environment
export APOLLONIA_ENV=test
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Start test infrastructure
docker-compose -f docker-compose.test.yml up -d

# Run tests
uv run pytest

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Unit Testing

Unit tests focus on testing individual components in isolation.

### Test Organization

```python
# tests/unit/test_ingestor.py
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from ingestor.file_monitor import FileMonitor
from ingestor.media_processor import MediaProcessor


class TestFileMonitor:
    """Test suite for FileMonitor class."""

    @pytest.fixture
    def monitor(self, tmp_path):
        """Create FileMonitor instance with temporary directory."""
        return FileMonitor(watch_path=tmp_path)

    def test_should_detect_new_audio_file(self, monitor, tmp_path):
        """Should detect when new audio file is added."""
        # Given
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 content")

        # When
        events = monitor.scan_for_changes()

        # Then
        assert len(events) == 1
        assert events[0].file_path == audio_file
        assert events[0].event_type == "file_created"

    def test_should_ignore_hidden_files(self, monitor, tmp_path):
        """Should ignore hidden files and temporary files."""
        # Given
        hidden_file = tmp_path / ".hidden.mp3"
        temp_file = tmp_path / "temp.tmp"
        hidden_file.write_bytes(b"content")
        temp_file.write_bytes(b"content")

        # When
        events = monitor.scan_for_changes()

        # Then
        assert len(events) == 0


class TestMediaProcessor:
    """Test suite for MediaProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create MediaProcessor instance."""
        return MediaProcessor()

    def test_should_extract_metadata_from_mp3(self, processor):
        """Should extract correct metadata from MP3 file."""
        # Given
        mp3_file = Path("fixtures/media/sample.mp3")

        # When
        metadata = processor.extract_metadata(mp3_file)

        # Then
        assert metadata.title == "Sample Song"
        assert metadata.artist == "Test Artist"
        assert metadata.duration == 180.5
        assert metadata.format == "mp3"

    @patch("ingestor.media_processor.hashlib")
    def test_should_compute_file_hashes(self, mock_hashlib, processor):
        """Should compute SHA256 and xxh128 hashes."""
        # Given
        mock_sha256 = Mock()
        mock_sha256.hexdigest.return_value = "sha256_hash"
        mock_hashlib.sha256.return_value = mock_sha256

        test_file = Path("fixtures/media/sample.mp3")

        # When
        hashes = processor.compute_hashes(test_file)

        # Then
        assert hashes.sha256 == "sha256_hash"
        assert hashes.xxh128 is not None
        mock_hashlib.sha256.assert_called_once()
```

### Mocking External Dependencies

```python
# tests/unit/test_populator.py
import pytest
from unittest.mock import Mock, AsyncMock, patch

from populator.database_client import DatabaseClient
from populator.message_consumer import MessageConsumer


class TestDatabaseClient:
    """Test suite for DatabaseClient class."""

    @pytest.fixture
    def mock_connection(self):
        """Mock database connection."""
        connection = AsyncMock()
        connection.execute.return_value = Mock(rowcount=1)
        return connection

    @pytest.fixture
    def db_client(self, mock_connection):
        """Create DatabaseClient with mocked connection."""
        client = DatabaseClient()
        client._connection = mock_connection
        return client

    @pytest.mark.asyncio
    async def test_should_insert_media_record(self, db_client, mock_connection):
        """Should insert media record into database."""
        # Given
        media_data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": "/data/test.mp3",
        }

        # When
        result = await db_client.insert_media(media_data)

        # Then
        assert result.success is True
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_handle_duplicate_insert(self, db_client, mock_connection):
        """Should handle duplicate key errors gracefully."""
        # Given
        mock_connection.execute.side_effect = Exception("Duplicate key")
        media_data = {"title": "Test", "file_path": "/data/test.mp3"}

        # When
        result = await db_client.insert_media(media_data)

        # Then
        assert result.success is False
        assert "Duplicate" in result.error_message
```

### Test Fixtures and Utilities

```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from tests.fixtures.media_generator import MediaFileGenerator


@pytest.fixture(scope="session")
def sample_media_files() -> Generator[Path, None, None]:
    """Generate sample media files for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    generator = MediaFileGenerator(temp_dir)

    # Generate test files
    generator.create_mp3_file("sample.mp3", duration=30)
    generator.create_wav_file("sample.wav", duration=15)
    generator.create_flac_file("sample.flac", duration=45)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_amqp_connection():
    """Mock AMQP connection for testing."""
    from unittest.mock import AsyncMock

    connection = AsyncMock()
    channel = AsyncMock()
    connection.channel.return_value = channel
    return connection, channel


@pytest.fixture
def test_database():
    """In-memory test database."""
    import sqlite3

    connection = sqlite3.connect(":memory:")

    # Create test schema
    connection.execute(
        """
        CREATE TABLE media (
            id TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            file_path TEXT UNIQUE
        )
    """
    )

    yield connection
    connection.close()
```

## Integration Testing

Integration tests verify interactions between components and external services.

### Database Integration Tests

```python
# tests/integration/test_database.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from populator.database_client import DatabaseClient
from populator.models import Media


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture(scope="class")
    async def database_client(self):
        """Create database client with test database."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        client = DatabaseClient(engine)
        await client.initialize_schema()
        return client

    @pytest.mark.asyncio
    async def test_full_media_workflow(self, database_client):
        """Test complete media CRUD workflow."""
        # Create
        media_data = {
            "title": "Integration Test Song",
            "artist": "Test Artist",
            "file_path": "/test/path.mp3",
            "duration": 180,
            "format": "mp3",
        }

        media_id = await database_client.create_media(media_data)
        assert media_id is not None

        # Read
        media = await database_client.get_media(media_id)
        assert media.title == "Integration Test Song"
        assert media.artist == "Test Artist"

        # Update
        await database_client.update_media(media_id, {"genre": "Rock"})
        updated_media = await database_client.get_media(media_id)
        assert updated_media.genre == "Rock"

        # Delete
        await database_client.delete_media(media_id)
        deleted_media = await database_client.get_media(media_id)
        assert deleted_media is None
```

### Message Queue Integration Tests

```python
# tests/integration/test_amqp_flow.py
import pytest
import asyncio
import json
from unittest.mock import AsyncMock

from ingestor.publisher import MessagePublisher
from populator.consumer import MessageConsumer


@pytest.mark.integration
class TestAMQPFlow:
    """Integration tests for AMQP message flow."""

    @pytest.fixture(scope="class")
    async def amqp_setup(self):
        """Set up AMQP broker for testing."""
        import aio_pika

        connection = await aio_pika.connect_robust("amqp://test:test@localhost/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange("apollonia_test", "fanout")
        queue = await channel.declare_queue("test_queue", auto_delete=True)
        await queue.bind(exchange)

        yield connection, channel, exchange, queue

        await connection.close()

    @pytest.mark.asyncio
    async def test_message_publishing_and_consumption(self, amqp_setup):
        """Test complete message publishing and consumption flow."""
        connection, channel, exchange, queue = amqp_setup

        # Set up publisher
        publisher = MessagePublisher(connection, exchange)

        # Set up consumer
        messages_received = []

        async def message_handler(message):
            data = json.loads(message.body.decode())
            messages_received.append(data)
            await message.ack()

        consumer = MessageConsumer(connection, queue, message_handler)

        # Start consuming
        consumer_task = asyncio.create_task(consumer.start())

        # Publish test message
        test_message = {
            "file_path": "/test/audio.mp3",
            "event_type": "file_created",
            "metadata": {"title": "Test Song", "artist": "Test Artist"},
        }

        await publisher.publish(test_message)

        # Wait for message processing
        await asyncio.sleep(0.1)

        # Verify message was received
        assert len(messages_received) == 1
        assert messages_received[0]["file_path"] == "/test/audio.mp3"
        assert messages_received[0]["metadata"]["title"] == "Test Song"

        # Cleanup
        consumer_task.cancel()
```

## End-to-End Testing

E2E tests verify complete user workflows across the entire system.

### API Endpoint Testing

```python
# tests/e2e/test_api_endpoints.py
import pytest
import httpx
import asyncio
from pathlib import Path


@pytest.mark.e2e
class TestAPIEndpoints:
    """End-to-end tests for API endpoints."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """HTTP client for API testing."""
        return httpx.AsyncClient(base_url="http://localhost:8000")

    @pytest.fixture(scope="class")
    async def auth_token(self, api_client):
        """Authenticate and get JWT token."""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_media_upload_workflow(self, api_client, auth_token):
        """Test complete media upload and processing workflow."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Upload media file
        test_file = Path("fixtures/media/sample.mp3")
        with open(test_file, "rb") as f:
            files = {"file": ("sample.mp3", f, "audio/mpeg")}
            data = {"metadata": '{"title": "E2E Test Song"}'}

            response = await api_client.post(
                "/api/v1/media/upload", headers=headers, files=files, data=data
            )

        assert response.status_code == 201
        media_data = response.json()
        media_id = media_data["id"]

        # Wait for processing to complete
        await asyncio.sleep(5)

        # Verify media details
        response = await api_client.get(f"/api/v1/media/{media_id}", headers=headers)
        assert response.status_code == 200

        media = response.json()
        assert media["title"] == "E2E Test Song"
        assert media["format"] == "mp3"
        assert "audio_features" in media
        assert media["audio_features"]["tempo"] is not None

        # Test search functionality
        response = await api_client.get(
            "/api/v1/search?q=E2E Test Song", headers=headers
        )
        assert response.status_code == 200

        search_results = response.json()
        assert len(search_results["items"]) >= 1
        assert any(item["id"] == media_id for item in search_results["items"])
```

### Full System Workflow Testing

```python
# tests/e2e/test_full_workflow.py
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path


@pytest.mark.e2e
class TestFullWorkflow:
    """End-to-end tests for complete system workflows."""

    @pytest.fixture(scope="class")
    async def system_setup(self):
        """Set up complete system for E2E testing."""
        # Start all services via Docker Compose
        import subprocess

        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.fail(f"Failed to start services: {result.stderr}")

        # Wait for services to be ready
        await asyncio.sleep(30)

        yield

        # Cleanup
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"]
        )

    @pytest.mark.asyncio
    async def test_file_monitoring_to_api_workflow(self, system_setup):
        """Test file monitoring → processing → API availability workflow."""
        # Create temporary directory for file monitoring
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Copy test file to monitored directory
            test_file = Path("fixtures/media/sample.mp3")
            target_file = temp_dir / "test_song.mp3"
            shutil.copy2(test_file, target_file)

            # Wait for file to be detected and processed
            await asyncio.sleep(10)

            # Verify file appears in API
            async with httpx.AsyncClient() as client:
                # Get auth token
                auth_response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={"username": "admin", "password": "admin123"},
                )
                token = auth_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Search for the processed file
                search_response = await client.get(
                    "http://localhost:8000/api/v1/search?q=test_song", headers=headers
                )

                assert search_response.status_code == 200
                results = search_response.json()
                assert len(results["items"]) >= 1

                # Verify audio features were extracted
                media_item = results["items"][0]
                assert "audio_features" in media_item
                assert media_item["audio_features"]["tempo"] is not None

        finally:
            shutil.rmtree(temp_dir)
```

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
import httpx
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.performance
class TestLoadPerformance:
    """Performance tests for load scenarios."""

    @pytest.mark.asyncio
    async def test_api_concurrent_requests(self):
        """Test API performance under concurrent load."""

        async def make_request(client, endpoint):
            start_time = time.time()
            response = await client.get(endpoint)
            end_time = time.time()
            return {"status": response.status_code, "duration": end_time - start_time}

        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Authenticate once
            auth_response = await client.post(
                "/api/v1/auth/login",
                json={"username": "test_user", "password": "test_password"},
            )
            token = auth_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {token}"})

            # Run concurrent requests
            tasks = []
            for _ in range(100):
                task = make_request(client, "/api/v1/media?limit=10")
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # Analyze results
            response_times = [r["duration"] for r in results]
            success_count = len([r for r in results if r["status"] == 200])

            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]

            # Performance assertions
            assert success_count >= 95  # 95% success rate
            assert avg_response_time < 0.5  # Average response time < 500ms
            assert p95_response_time < 1.0  # 95th percentile < 1s

    @pytest.mark.slow
    def test_bulk_upload_performance(self):
        """Test performance of bulk media uploads."""
        # Test uploading multiple files simultaneously
        pass
```

### Memory and Resource Testing

```python
# tests/performance/test_resources.py
import pytest
import psutil
import time
from pathlib import Path


@pytest.mark.performance
class TestResourceUsage:
    """Tests for memory and resource usage."""

    def test_memory_usage_during_processing(self):
        """Monitor memory usage during file processing."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Trigger processing of large file
        large_file = Path("fixtures/media/large_audio.wav")
        # ... process file ...

        # Monitor memory for memory leaks
        time.sleep(5)
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Assert memory increase is reasonable
        max_allowed_increase = 200 * 1024 * 1024  # 200MB
        assert memory_increase < max_allowed_increase
```

## Testing Best Practices

### Test Organization

1. **Descriptive Test Names**: Use `test_should_<expected_behavior>_when_<condition>` format
1. **Given-When-Then Structure**: Organize test logic clearly
1. **Single Assertion**: Focus each test on one specific behavior
1. **Test Independence**: Tests should not depend on each other

### Mocking Guidelines

```python
# Good: Mock external dependencies
@patch("ingestor.external_service.AudioAnalyzer")
def test_should_handle_analyzer_failure(self, mock_analyzer):
    mock_analyzer.analyze.side_effect = Exception("Service unavailable")
    # Test error handling
    pass


# Bad: Mock internal logic (tests implementation details)
@patch("ingestor.media_processor.MediaProcessor._internal_method")
def test_something(self, mock_method):
    # This makes tests brittle
    pass
```

### Test Data Management

```python
# Use factories for test data
class MediaFactory:
    @staticmethod
    def create_audio_metadata(**kwargs):
        defaults = {
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "format": "mp3",
        }
        defaults.update(kwargs)
        return defaults


# Use parametrized tests for multiple scenarios
@pytest.mark.parametrize(
    "file_format,expected_type",
    [("mp3", "audio"), ("wav", "audio"), ("mp4", "video"), ("avi", "video")],
)
def test_should_detect_media_type(self, file_format, expected_type):
    # Test implementation
    pass
```

## Continuous Integration

### GitHub Actions Integration

Tests are automatically run in GitHub Actions:

```yaml
# .github/workflows/test.yml
- name: 🧪 Run Python tests
  run: |
    uv run pytest tests/unit tests/integration \
      --cov=src \
      --cov-report=xml \
      --cov-report=term \
      --junit-xml=pytest-results.xml

- name: 🧪 Run E2E tests
  run: |
    docker-compose -f docker-compose.test.yml up -d
    sleep 30
    uv run pytest tests/e2e --tb=short
    docker-compose -f docker-compose.test.yml down -v
```

### Test Coverage Requirements

- **Minimum Coverage**: 80% for new code
- **Critical Paths**: 95% coverage required
- **Coverage Reports**: Generated for each PR

### Quality Gates

Tests must pass all quality gates:

1. ✅ Unit tests (100% pass rate)
1. ✅ Integration tests (100% pass rate)
1. ✅ Code coverage (≥80%)
1. ✅ E2E tests (critical paths)
1. ✅ Performance tests (within thresholds)
1. ✅ Security tests (no high/critical issues)

## Debugging Tests

### Common Issues

```bash
# Test isolation issues
pytest --forked  # Run tests in separate processes

# Database state issues
pytest --create-db  # Recreate test database

# Timing issues in async tests
pytest -s tests/integration/  # Show output for debugging

# Memory issues
pytest --no-cov  # Disable coverage for faster execution
```

### Test Debugging Tools

```python
# Add breakpoints in tests
import pdb

pdb.set_trace()


# Use pytest fixtures for debugging
@pytest.fixture
def debug_mode():
    import logging

    logging.basicConfig(level=logging.DEBUG)


# Capture logs in tests
def test_with_logs(caplog):
    # Test code
    assert "Expected log message" in caplog.text
```

For more information on development practices, see the [Development Guide](development-guide.md) and
[Contributing Guide](../../CONTRIBUTING.md).
