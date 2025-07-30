"""Test API endpoints in detail."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.schemas.catalog import MediaFile, MediaType


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j session."""
    with patch("api.database.get_neo4j_session") as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    with patch("api.utils.cache.get_cache_client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_media_file():
    """Create a sample media file."""
    return MediaFile(
        id="test-123",
        path="/data/test.mp3",
        filename="test.mp3",
        media_type=MediaType.AUDIO,
        size=1024000,
        sha256_hash="abc123",
        xxh128_hash="def456",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        accessed_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
    )


class TestMediaEndpoints:
    """Test media-related endpoints."""

    def test_get_media_file(self, client, mock_neo4j_session, sample_media_file):
        """Test getting a single media file."""
        # Mock Neo4j response
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": sample_media_file.model_dump()})
        )

        response = client.get(f"/api/v1/media/{sample_media_file.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_media_file.id
        assert data["filename"] == sample_media_file.filename

    def test_get_media_file_not_found(self, client, mock_neo4j_session):
        """Test getting a non-existent media file."""
        mock_neo4j_session.run.return_value = Mock(single=Mock(return_value=None))

        response = client.get("/api/v1/media/non-existent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_media_files_with_pagination(self, client, mock_neo4j_session):
        """Test listing media files with pagination."""
        # Mock Neo4j response
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(
                return_value=[
                    {"file": {"id": "1", "filename": "test1.mp3"}},
                    {"file": {"id": "2", "filename": "test2.mp3"}},
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

    def test_create_media_file(self, client, mock_neo4j_session):
        """Test creating a new media file."""
        new_file = {
            "path": "/data/new.mp3",
            "filename": "new.mp3",
            "media_type": "audio",
            "size": 2048000,
            "sha256_hash": "xyz789",
            "xxh128_hash": "uvw456",
        }

        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {**new_file, "id": "new-123"}})
        )

        response = client.post("/api/v1/media", json=new_file)
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == new_file["filename"]
        assert "id" in data

    def test_update_media_file(self, client, mock_neo4j_session, sample_media_file):
        """Test updating a media file."""
        update_data = {"size": 2048000}

        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {**sample_media_file.model_dump(), **update_data}})
        )

        response = client.patch(f"/api/v1/media/{sample_media_file.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["size"] == update_data["size"]

    def test_delete_media_file(self, client, mock_neo4j_session):
        """Test deleting a media file."""
        mock_neo4j_session.run.return_value = Mock(single=Mock(return_value={"deleted": True}))

        response = client.delete("/api/v1/media/test-123")
        assert response.status_code == 204


class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_with_filters(self, client, mock_neo4j_session):
        """Test search with various filters."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(return_value=[{"file": {"id": "1", "filename": "result.mp3"}}])
        )

        response = client.get(
            "/api/v1/catalog/search",
            params={"q": "test", "media_type": "audio", "min_size": 1000, "max_size": 10000000},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert len(data["results"]) == 1

    def test_search_with_date_range(self, client, mock_neo4j_session):
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

    def test_search_with_sorting(self, client, mock_neo4j_session):
        """Test search with sorting options."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(
                return_value=[
                    {"file": {"id": "1", "filename": "a.mp3", "size": 2000}},
                    {"file": {"id": "2", "filename": "b.mp3", "size": 1000}},
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

    def test_cached_response(self, client, mock_neo4j_session, mock_redis_client):
        """Test that responses are cached."""
        # First call - cache miss
        mock_redis_client.get.return_value = None
        mock_neo4j_session.run.return_value = Mock(data=Mock(return_value=[]))

        response1 = client.get("/api/v1/catalog/media")
        assert response1.status_code == 200

        # Verify cache was set
        mock_redis_client.setex.assert_called_once()

    def test_cache_invalidation(self, client, mock_neo4j_session, mock_redis_client):
        """Test cache invalidation on updates."""
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(return_value={"file": {"id": "test-123"}})
        )

        # Create a new file
        response = client.post(
            "/api/v1/media",
            json={
                "path": "/data/new.mp3",
                "filename": "new.mp3",
                "media_type": "audio",
                "size": 1024,
            },
        )
        assert response.status_code == 201

        # Verify cache was cleared
        mock_redis_client.delete.assert_called()


class TestErrorScenarios:
    """Test error handling scenarios."""

    def test_database_connection_error(self, client):
        """Test handling of database connection errors."""
        with patch("api.database.get_neo4j_session") as mock:
            mock.side_effect = Exception("Connection failed")

            response = client.get("/api/v1/catalog/media")
            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()

    def test_invalid_media_type(self, client):
        """Test validation of invalid media type."""
        response = client.post(
            "/api/v1/media",
            json={
                "path": "/data/test.xyz",
                "filename": "test.xyz",
                "media_type": "invalid",
                "size": 1024,
            },
        )
        assert response.status_code == 422

    def test_rate_limiting(self, client, mock_redis_client):
        """Test rate limiting functionality."""
        # Simulate rate limit exceeded
        mock_redis_client.incr.return_value = 101  # Over limit
        mock_redis_client.ttl.return_value = 60

        response = client.get("/api/v1/catalog/media")
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
