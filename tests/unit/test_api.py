"""Unit tests for API components."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch

from api.config import Settings
from api.database import get_session
from api.schemas.catalog import MediaFileResponse
from api.schemas.search import SearchResult
from api.utils.logging import setup_logging


class TestConfig:
    """Test API configuration."""

    def test_settings_defaults(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Apollonia API"
        assert settings.debug is False
        assert settings.api_v1_prefix == "/api/v1"

    def test_settings_from_env(self, monkeypatch: MonkeyPatch) -> None:
        """Test settings from environment variables."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test@localhost/test")
        monkeypatch.setenv("REDIS_URL", "redis://test:6379")

        settings = Settings()
        assert settings.debug is True
        assert settings.database_url == "postgresql+asyncpg://test@localhost/test"
        assert settings.redis_url == "redis://test:6379"


class TestDatabase:
    """Test database utilities."""

    @pytest.mark.asyncio
    async def test_get_session(self) -> None:
        """Test database session creation."""
        with patch("api.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            async for session in get_session():
                assert session is not None


class TestSchemas:
    """Test API schemas."""

    def test_media_file_response_schema(self) -> None:
        """Test MediaFileResponse schema."""
        media = MediaFileResponse(
            id=uuid4(),
            catalog_id=uuid4(),
            file_name="test.mp3",
            file_path="/data/test.mp3",
            file_size=1024,
            media_type="audio",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert media.file_name == "test.mp3"
        assert media.media_type == "audio"
        assert media.file_size == 1024

    def test_search_result_schema(self) -> None:
        """Test SearchResult schema."""
        result = SearchResult(
            id=uuid4(),
            catalog_id=uuid4(),
            file_name="test.mp3",
            file_size=1024,
            media_type="audio",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert result.file_name == "test.mp3"
        assert result.file_size == 1024


class TestUtils:
    """Test utility functions."""

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        setup_logging()
        # setup_logging doesn't return anything, just sets up logging

    def test_emoji_utils(self) -> None:
        """Test emoji utilities."""
        from api.utils.emoji import MEDIA_EMOJI, STATUS_EMOJI

        assert MEDIA_EMOJI["audio"] == "🎵"
        assert MEDIA_EMOJI["video"] == "🎬"
        assert MEDIA_EMOJI["image"] == "🖼️"
        assert MEDIA_EMOJI["document"] == "📄"

        assert STATUS_EMOJI["success"] == "✅"
        assert STATUS_EMOJI["error"] == "❌"
        assert STATUS_EMOJI["warning"] == "⚠️"
