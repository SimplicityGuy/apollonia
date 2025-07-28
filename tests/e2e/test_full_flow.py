"""End-to-end tests for the complete Apollonia media processing flow."""

import asyncio
import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import aiohttp
import pytest
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# Test configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "http://localhost:15672")
POSTGRES_URL = os.getenv(
    "DATABASE_URL", "postgresql://apollonia:apollonia@localhost:5432/apollonia"
)


@pytest.fixture(scope="session")
def test_media_files() -> Iterator[dict[str, Path]]:
    """Create test media files for upload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test audio file (empty for testing)
        audio_file = Path(tmpdir) / "test_audio.mp3"
        audio_file.write_bytes(b"fake mp3 content")

        # Create test video file
        video_file = Path(tmpdir) / "test_video.mp4"
        video_file.write_bytes(b"fake mp4 content")

        yield {"audio": audio_file, "video": video_file}


@pytest.fixture(scope="session")
async def auth_token() -> str:
    """Get authentication token for API requests."""
    async with aiohttp.ClientSession() as session:
        # Register test user
        user_data = {"username": "testuser", "email": "test@example.com", "password": "testpass123"}

        # Try to register (might already exist)
        try:
            async with session.post(f"{API_URL}/api/v1/auth/register", json=user_data) as resp:
                await resp.json()
        except Exception:
            logger.debug("🔐 User registration failed (user might already exist)")

        # Login
        login_data = {"username": "testuser", "password": "testpass123"}
        async with session.post(f"{API_URL}/api/v1/auth/login", data=login_data) as resp:
            result = await resp.json()
            return str(result["access_token"])


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Test that all services are healthy."""
    async with aiohttp.ClientSession() as session:
        # Check API health
        async with session.get(f"{API_URL}/health") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "healthy"

        # Check RabbitMQ management API
        auth = aiohttp.BasicAuth("apollonia", "apollonia")
        async with session.get(f"{RABBITMQ_URL}/api/overview", auth=auth) as resp:
            assert resp.status == 200


@pytest.mark.asyncio
async def test_file_upload_and_processing(
    test_media_files: dict[str, Path], auth_token: str
) -> None:
    """Test complete file upload and processing flow."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
        # Upload audio file
        with test_media_files["audio"].open("rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename="test_audio.mp3", content_type="audio/mpeg")

            async with session.post(
                f"{API_URL}/api/v1/media/upload", data=data, headers=headers
            ) as resp:
                assert resp.status == 200
                upload_result = await resp.json()
                audio_file_id = upload_result["id"]

        # Wait for processing
        await asyncio.sleep(5)

        # Check file status
        async with session.get(
            f"{API_URL}/api/v1/media/files/{audio_file_id}", headers=headers
        ) as resp:
            assert resp.status == 200
            file_data = await resp.json()
            assert file_data["filename"] == "test_audio.mp3"
            assert file_data["media_type"] == "audio"
            # Processing might still be in progress
            assert file_data["processing_status"] in ["pending", "processing", "completed"]


@pytest.mark.asyncio
async def test_catalog_operations(auth_token: str) -> None:
    """Test catalog creation and management."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
        # Create catalog
        catalog_data = {"name": "Test Catalog", "description": "E2E test catalog"}
        async with session.post(
            f"{API_URL}/api/v1/catalogs", json=catalog_data, headers=headers
        ) as resp:
            assert resp.status == 200
            catalog = await resp.json()
            catalog_id = catalog["id"]

        # List catalogs
        async with session.get(f"{API_URL}/api/v1/catalogs", headers=headers) as resp:
            assert resp.status == 200
            catalogs = await resp.json()
            assert any(c["id"] == catalog_id for c in catalogs["items"])

        # Get specific catalog
        async with session.get(f"{API_URL}/api/v1/catalogs/{catalog_id}", headers=headers) as resp:
            assert resp.status == 200
            catalog_detail = await resp.json()
            assert catalog_detail["name"] == "Test Catalog"


@pytest.mark.asyncio
async def test_graphql_query(auth_token: str) -> None:
    """Test GraphQL endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    query = """
    query {
        files(limit: 10) {
            items {
                id
                filename
                mediaType
                fileSize
            }
            total
        }
    }
    """

    async with (
        aiohttp.ClientSession() as session,
        session.post(f"{API_URL}/graphql", json={"query": query}, headers=headers) as resp,
    ):
        assert resp.status == 200
        result = await resp.json()
        assert "data" in result
        assert "files" in result["data"]


@pytest.mark.asyncio
async def test_analytics_endpoint(auth_token: str) -> None:
    """Test analytics data retrieval."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with (
        aiohttp.ClientSession() as session,
        session.get(f"{API_URL}/api/v1/analytics", headers=headers) as resp,
    ):
        assert resp.status == 200
        analytics = await resp.json()
        assert "total_files" in analytics
        assert "total_storage" in analytics
        assert "media_types" in analytics


@pytest.mark.asyncio
async def test_search_functionality(auth_token: str) -> None:
    """Test media file search."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with aiohttp.ClientSession() as session:
        # Search for files
        params = {"q": "test", "media_type": "audio"}
        async with session.get(
            f"{API_URL}/api/v1/media/search", params=params, headers=headers
        ) as resp:
            assert resp.status == 200
            results = await resp.json()
            assert "items" in results
            assert "total" in results


@pytest.mark.skip(reason="This test expects PostgreSQL but the project uses Neo4j")
def test_database_schema() -> None:
    """Verify database schema is correctly set up."""
    engine = create_engine(POSTGRES_URL)

    with engine.connect() as conn:
        # Check tables exist
        result = conn.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        )

        tables = {row[0] for row in result}
        expected_tables = {"media_files", "media_features", "users", "catalogs", "catalog_files"}

        assert expected_tables.issubset(tables)


@pytest.mark.asyncio
async def test_concurrent_uploads(test_media_files: dict[str, Path], auth_token: str) -> None:
    """Test handling of concurrent file uploads."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    async def upload_file(session: aiohttp.ClientSession, file_path: Path, filename: str) -> Any:
        with file_path.open("rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename=filename)

            async with session.post(
                f"{API_URL}/api/v1/media/upload", data=data, headers=headers
            ) as resp:
                return resp.status, await resp.json()

    async with aiohttp.ClientSession() as session:
        # Upload multiple files concurrently
        tasks = []
        for i in range(5):
            task = upload_file(session, test_media_files["audio"], f"concurrent_test_{i}.mp3")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All uploads should succeed
        for status, data in results:
            assert status == 200
            assert "id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
