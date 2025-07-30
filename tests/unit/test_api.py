"""Unit tests for API components."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from api.config import Settings
from api.database import get_db_session
from api.schemas.catalog import MediaFile, MediaType
from api.schemas.search import SearchResult
from api.utils.cache import get_cache_client
from api.utils.logging import setup_logging


class TestConfig:
    """Test API configuration."""

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Apollonia API"
        assert settings.debug is False
        assert settings.api_v1_prefix == "/api/v1"

    def test_settings_from_env(self, monkeypatch):
        """Test settings from environment variables."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("NEO4J_URI", "bolt://test:7687")
        monkeypatch.setenv("REDIS_URL", "redis://test:6379")

        settings = Settings()
        assert settings.debug is True
        assert settings.neo4j_uri == "bolt://test:7687"
        assert settings.redis_url == "redis://test:6379"


class TestDatabase:
    """Test database utilities."""

    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """Test database session creation."""
        with patch("api.database.AsyncSession"):
            async with get_db_session() as session:
                assert session is not None


class TestCache:
    """Test cache utilities."""

    @pytest.mark.asyncio
    async def test_get_cache_client(self):
        """Test cache client creation."""
        with patch("api.utils.cache.Redis"):
            client = await get_cache_client()
            assert client is not None


class TestSchemas:
    """Test API schemas."""

    def test_media_file_schema(self):
        """Test MediaFile schema."""
        media = MediaFile(
            id="test-id",
            path="/data/test.mp3",
            filename="test.mp3",
            media_type=MediaType.AUDIO,
            size=1024,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert media.id == "test-id"
        assert media.media_type == MediaType.AUDIO
        assert media.size == 1024

    def test_search_result_schema(self):
        """Test SearchResult schema."""
        result = SearchResult(query="test", results=[], total=0, took_ms=10.5)
        assert result.query == "test"
        assert result.total == 0
        assert result.took_ms == 10.5


class TestUtils:
    """Test utility functions."""

    def test_setup_logging(self):
        """Test logging setup."""
        logger = setup_logging("test-logger")
        assert logger is not None
        assert logger.name == "test-logger"

    def test_emoji_utils(self):
        """Test emoji utilities."""
        from api.utils.emoji import get_file_emoji, get_status_emoji

        assert get_file_emoji("test.mp3") == "🎵"
        assert get_file_emoji("test.mp4") == "🎬"
        assert get_file_emoji("test.jpg") == "🖼️"
        assert get_file_emoji("test.txt") == "📄"

        assert get_status_emoji("success") == "✅"
        assert get_status_emoji("error") == "❌"
        assert get_status_emoji("warning") == "⚠️"
