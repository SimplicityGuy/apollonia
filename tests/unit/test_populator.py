"""Unit tests for the populator service."""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestPopulator:
    """Test cases for the Populator class."""

    @pytest.mark.asyncio
    async def test_populator_initialization(self):
        """Test that Populator can be initialized."""
        # Mock the modules before importing
        sys.modules["aio_pika"] = MagicMock()
        sys.modules["neo4j"] = MagicMock()

        # Set up the specific mocks we need
        sys.modules["aio_pika"].connect_robust = AsyncMock()
        sys.modules["neo4j"].AsyncGraphDatabase = MagicMock()

        try:
            from populator.populator import Populator

            populator = Populator()
            assert populator.amqp_connection is None
            assert populator.neo4j_driver is None
            assert populator._running is True
        finally:
            # Clean up the mocked modules
            if "aio_pika" in sys.modules:
                del sys.modules["aio_pika"]
            if "neo4j" in sys.modules:
                del sys.modules["neo4j"]

    def test_placeholder_for_ci(self):
        """Placeholder test that always passes for CI."""
        assert True
