"""Test API endpoints in detail."""

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_session() -> Generator[AsyncMock, None, None]:
    """Mock Neo4j session."""
    with patch("api.database.get_neo4j_session") as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session


@pytest.fixture
def mock_redis_client() -> Generator[AsyncMock, None, None]:
    """Mock Redis client."""
    with patch("api.utils.cache.get_cache_client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_media_file() -> dict[str, Any]:
    """Create a sample media file."""
    return {
        "id": "test-123",
        "file_path": "/data/test.mp3",
        "file_name": "test.mp3",
        "media_type": "audio",
        "file_size": 1024000,
        "hash_sha256": "abc123",
        "hash_xxh128": "def456",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "catalog_id": "00000000-0000-0000-0000-000000000000",
        "mime_type": "audio/mpeg",
        "metadata": {},
        "status": "active",
    }


class TestMediaEndpoints:
    """Test media-related endpoints."""

    def test_get_media_file(
        self, client: TestClient, mock_neo4j_session: AsyncMock, sample_media_file: dict[str, Any]
    ) -> None:
        """Test getting a single media file."""
        # Mock Neo4j response
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": sample_media_file})
        )

        response = client.get(f"/api/v1/media/{sample_media_file['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_media_file["id"]
        assert data["file_name"] == sample_media_file["file_name"]

    def test_get_media_file_not_found(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test getting a non-existent media file."""
        mock_neo4j_session.run.return_value = Mock(single=Mock(return_value=None))

        response = client.get("/api/v1/media/non-existent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_media_files_with_pagination(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test listing media files with pagination."""
        # Mock Neo4j response
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(
                return_value=[
                    {"file": {"id": "1", "file_name": "test1.mp3"}},
                    {"file": {"id": "2", "file_name": "test2.mp3"}},
                ]
            )
        )

        response = client.get("/api/v1/catalog/media?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_create_media_file(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test creating a new media file."""
        new_file = {
            "file_path": "/data/new.mp3",
            "file_name": "new.mp3",
            "media_type": "audio",
            "file_size": 2048000,
            "hash_sha256": "xyz789",
            "hash_xxh128": "uvw456",
        }

        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {**new_file, "id": "new-123"}})
        )

        response = client.post("/api/v1/media", json=new_file)
        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == new_file["file_name"]
        assert "id" in data

    def test_update_media_file(
        self, client: TestClient, mock_neo4j_session: AsyncMock, sample_media_file: dict[str, Any]
    ) -> None:
        """Test updating a media file."""
        update_data = {"file_size": 2048000}

        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {**sample_media_file, **update_data}})
        )

        response = client.patch(f"/api/v1/media/{sample_media_file['id']}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["file_size"] == update_data["file_size"]

    def test_delete_media_file(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test deleting a media file."""
        mock_neo4j_session.run.return_value = Mock(single=Mock(return_value={"deleted": True}))

        response = client.delete("/api/v1/media/test-123")
        assert response.status_code == 204


class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_with_filters(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test search with various filters."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(return_value=[{"file": {"id": "1", "file_name": "result.mp3"}}])
        )

        response = client.get(
            "/api/v1/catalog/search",
            params={"q": "test", "media_type": "audio", "min_size": 1000, "max_size": 10000000},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert len(data["results"]) == 1

    def test_search_with_date_range(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test search with date range filters."""
        mock_neo4j_session.run.return_value = Mock(data=Mock(return_value=[]))

        response = client.get(
            "/api/v1/catalog/search",
            params={
                "q": "recent",
                "created_after": "2024-01-01T00:00:00Z",
                "created_before": "2024-12-31T23:59:59Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "recent"

    def test_search_with_sorting(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test search with sorting options."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(
                return_value=[
                    {"file": {"id": "1", "file_name": "a.mp3", "file_size": 2000}},
                    {"file": {"id": "2", "file_name": "b.mp3", "file_size": 1000}},
                ]
            )
        )

        response = client.get(
            "/api/v1/catalog/search", params={"q": "test", "sort_by": "size", "sort_order": "desc"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2


class TestCacheIntegration:
    """Test cache integration."""

    def test_cached_response(
        self, client: TestClient, mock_neo4j_session: AsyncMock, mock_redis_client: AsyncMock
    ) -> None:
        """Test that responses are cached."""
        # First call - cache miss
        mock_redis_client.get.return_value = None
        mock_neo4j_session.run.return_value = Mock(data=Mock(return_value=[]))

        response1 = client.get("/api/v1/catalog/media")
        assert response1.status_code == 200

        # Verify cache was set
        mock_redis_client.setex.assert_called_once()

    def test_cache_invalidation(
        self, client: TestClient, mock_neo4j_session: AsyncMock, mock_redis_client: AsyncMock
    ) -> None:
        """Test cache invalidation on updates."""
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {"id": "test-123"}})
        )

        # Create a new file
        response = client.post(
            "/api/v1/media",
            json={
                "file_path": "/data/new.mp3",
                "file_name": "new.mp3",
                "media_type": "audio",
                "file_size": 1024,
            },
        )
        assert response.status_code == 201

        # Verify cache was cleared
        mock_redis_client.delete.assert_called()


class TestErrorScenarios:
    """Test error handling scenarios."""

    def test_database_connection_error(self, client: TestClient) -> None:
        """Test handling of database connection errors."""
        with patch("api.database.get_neo4j_session") as mock:
            mock.side_effect = Exception("Connection failed")

            response = client.get("/api/v1/catalog/media")
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()

    def test_invalid_media_type(self, client: TestClient) -> None:
        """Test validation of invalid media type."""
        response = client.post(
            "/api/v1/media",
            json={
                "file_path": "/data/test.xyz",
                "file_name": "test.xyz",
                "media_type": "invalid",
                "file_size": 1024,
            },
        )
        assert response.status_code == 422

    def test_rate_limiting(self, client: TestClient, mock_redis_client: AsyncMock) -> None:
        """Test rate limiting functionality."""
        # Simulate rate limit exceeded
        mock_redis_client.incr.return_value = 101  # Over limit
        mock_redis_client.ttl.return_value = 60

        response = client.get("/api/v1/catalog/media")
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
