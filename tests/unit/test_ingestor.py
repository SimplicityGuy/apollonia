"""Unit tests for the ingestor service."""

import sys
from unittest.mock import AsyncMock, patch

import pytest


class TestIngestor:
    """Test cases for the Ingestor class."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    async def test_ingestor_initialization(self):
        """Test that Ingestor can be initialized."""
        # Mock all the dependencies before importing
        with (
            patch("ingestor.ingestor.aio_pika.connect", new_callable=AsyncMock),
            patch("ingestor.ingestor.asyncinotify.Inotify"),
            patch("ingestor.ingestor.asyncinotify.Mask"),
        ):
            from ingestor.ingestor import Ingestor

            ingestor = Ingestor(
                amqp_url="amqp://test:test@localhost:5672/", data_directory="/test/data"
            )
            assert ingestor.amqp_url == "amqp://test:test@localhost:5672/"
            assert ingestor.data_directory == "/test/data"

    def test_placeholder_for_ci(self):
        """Placeholder test that always passes for CI."""
        assert True
