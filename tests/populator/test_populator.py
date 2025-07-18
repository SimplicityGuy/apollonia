"""Tests for the Populator service."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import orjson
import pytest
from aio_pika.abc import AbstractIncomingMessage

from populator.populator import Populator, main, print_banner, setup_logging


class MockMessage(AbstractIncomingMessage):
    """Mock implementation of AbstractIncomingMessage for testing."""

    def __init__(self, body: bytes) -> None:
        self._body = body
        self.processed = False
        self.acked = False
        self.nacked = False
        self.rejected = False

    @property
    def body(self) -> bytes:
        return self._body

    async def ack(self, _multiple: bool = False) -> None:
        self.acked = True

    async def nack(self, _multiple: bool = False, _requeue: bool = True) -> None:
        self.nacked = True

    async def reject(self, _requeue: bool = False) -> None:
        self.rejected = True

    async def process(self, *_args, **_kwargs):
        """Context manager for processing."""

        class ProcessContext:
            async def __aenter__(self_):
                return self_

            async def __aexit__(self_, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    await self.ack()
                else:
                    await self.nack(requeue=True)
                return False

        return ProcessContext()

    # Required properties for AbstractIncomingMessage
    @property
    def message_count(self) -> int:
        return 0

    @property
    def delivery(self) -> Any:
        return Mock()

    @property
    def redelivered(self) -> bool:
        return False

    @property
    def channel(self) -> Any:
        return Mock()


class TestPopulator:
    """Test cases for the Populator class."""

    def test_init(self) -> None:
        """Test Populator initialization."""
        populator = Populator()

        assert populator.amqp_connection is None
        assert populator.neo4j_driver is None
        assert populator._running is True

    @pytest.mark.asyncio
    @patch("populator.populator.AsyncGraphDatabase")
    @patch("populator.populator.connect_robust")
    async def test_aenter(self, mock_connect: Mock, mock_neo4j: Mock) -> None:
        """Test async context manager enter."""
        # Setup mocks
        mock_amqp_conn = AsyncMock()
        mock_connect.return_value = mock_amqp_conn

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_neo4j.driver.return_value = mock_driver

        populator = Populator()
        result = await populator.__aenter__()

        # Verify connections
        mock_connect.assert_called_once()
        mock_neo4j.driver.assert_called_once()
        assert populator.amqp_connection == mock_amqp_conn
        assert populator.neo4j_driver == mock_driver
        assert result == populator

        # Verify Neo4j connection test
        mock_session.run.assert_awaited_once_with("RETURN 1")

    @pytest.mark.asyncio
    async def test_aexit(self) -> None:
        """Test async context manager exit."""
        populator = Populator()
        mock_amqp = AsyncMock()
        mock_neo4j = AsyncMock()
        populator.amqp_connection = mock_amqp
        populator.neo4j_driver = mock_neo4j

        await populator.__aexit__(None, None, None)

        mock_amqp.close.assert_awaited_once()
        mock_neo4j.close.assert_awaited_once()

    def test_stop(self) -> None:
        """Test stop method."""
        populator = Populator()
        assert populator._running is True

        populator.stop()

        assert populator._running is False

    @pytest.mark.asyncio
    async def test_process_message_success(self) -> None:
        """Test successful message processing."""
        # Create test data
        test_data = {
            "file_path": "/data/test.txt",
            "sha256_hash": "abc123",
            "xxh128_hash": "def456",
            "size": 1024,
            "timestamp": "2024-01-01T12:00:00+00:00",
            "neighbors": ["/data/test.log"],
        }

        # Create mock message
        message = MockMessage(orjson.dumps(test_data))

        # Create populator with mocked import method
        populator = Populator()
        populator._import_to_neo4j = AsyncMock()

        await populator.process_message(message)

        # Verify
        populator._import_to_neo4j.assert_awaited_once_with(test_data)
        assert message.acked is True
        assert message.nacked is False

    @pytest.mark.asyncio
    async def test_process_message_error(self) -> None:
        """Test message processing with error."""
        # Create invalid message
        message = MockMessage(b"invalid json")

        populator = Populator()
        populator._import_to_neo4j = AsyncMock()

        # Process should handle error gracefully
        await populator.process_message(message)

        # Verify message was nacked due to error
        assert message.acked is False
        assert message.nacked is True
        populator._import_to_neo4j.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_import_to_neo4j(self) -> None:
        """Test Neo4j import functionality."""
        # Test data
        test_data = {
            "file_path": "/data/test.txt",
            "sha256_hash": "abc123",
            "xxh128_hash": "def456",
            "size": 1024,
            "modified_time": "2024-01-01T10:00:00+00:00",
            "accessed_time": "2024-01-01T11:00:00+00:00",
            "changed_time": "2024-01-01T09:00:00+00:00",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "event_type": "IN_CREATE",
            "neighbors": ["/data/test.log", "/data/test.txt.bak"],
        }

        # Mock Neo4j driver and session
        mock_result = AsyncMock()
        mock_result.single.return_value = {"f": {"path": "/data/test.txt"}}

        mock_session = AsyncMock()
        mock_session.run.return_value = mock_result

        mock_driver = AsyncMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session

        populator = Populator()
        populator.neo4j_driver = mock_driver

        await populator._import_to_neo4j(test_data)

        # Verify main node creation
        assert mock_session.run.await_count >= 1
        main_query_call = mock_session.run.await_args_list[0]
        assert "MERGE (f:File {path: $file_path})" in main_query_call[0][0]

        # Verify neighbor relationships were created
        # Should have 1 main query + 2 neighbor queries = 3 total
        assert mock_session.run.await_count == 3

    @pytest.mark.asyncio
    async def test_import_to_neo4j_no_driver(self) -> None:
        """Test import when Neo4j driver is not available."""
        populator = Populator()
        populator.neo4j_driver = None

        # Should return without error
        await populator._import_to_neo4j({"file_path": "/test.txt"})

    @pytest.mark.asyncio
    @patch("populator.populator.logger")
    async def test_import_to_neo4j_with_minimal_data(self, _mock_logger: Mock) -> None:
        """Test import with minimal data (missing optional fields)."""
        # Minimal data
        test_data = {"file_path": "/data/minimal.txt", "timestamp": "2024-01-01T12:00:00+00:00"}

        # Mock Neo4j
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single.return_value = {"f": {"path": "/data/minimal.txt"}}
        mock_session.run.return_value = mock_result

        mock_driver = AsyncMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session

        populator = Populator()
        populator.neo4j_driver = mock_driver

        await populator._import_to_neo4j(test_data)

        # Verify query was called with defaults
        call_args = mock_session.run.await_args_list[0][1]
        assert call_args["sha256_hash"] == ""
        assert call_args["xxh128_hash"] == ""
        assert call_args["size"] == 0

    @pytest.mark.asyncio
    async def test_consume(self) -> None:
        """Test message consumption."""
        # Mock AMQP connection and channel
        mock_queue = AsyncMock()
        mock_iterator = AsyncMock()

        # Create messages
        messages = [
            MockMessage(orjson.dumps({"file_path": f"/data/file{i}.txt"})) for i in range(3)
        ]

        # Setup async iteration
        async def mock_aiter():
            for msg in messages:
                if not populator._running:
                    break
                yield msg
            populator._running = False

        mock_iterator.__aiter__ = mock_aiter
        mock_queue.iterator.return_value.__aenter__.return_value = mock_iterator

        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_channel.declare_queue.return_value = mock_queue

        mock_connection = AsyncMock()
        mock_connection.channel.return_value = mock_channel

        populator = Populator()
        populator.amqp_connection = mock_connection
        populator.process_message = AsyncMock()

        await populator.consume()

        # Verify setup
        mock_channel.declare_exchange.assert_awaited_once_with(
            "apollonia", type="fanout", durable=True, auto_delete=False
        )
        mock_channel.declare_queue.assert_awaited_once_with(
            "apollonia-populator", durable=True, auto_delete=False
        )
        mock_queue.bind.assert_awaited_once()

        # Verify messages were processed
        assert populator.process_message.await_count == 3

    @pytest.mark.asyncio
    async def test_consume_no_connection(self) -> None:
        """Test consume when no connection available."""
        populator = Populator()
        populator.amqp_connection = None

        # Should return without error
        await populator.consume()


class TestMainFunctions:
    """Test main functions and entry points."""

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("populator.populator.logging.basicConfig") as mock_config:
            setup_logging()

            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args["level"] == "INFO"
            assert "%(asctime)s" in call_args["format"]

    def test_print_banner(self, capsys: pytest.CaptureFixture) -> None:
        """Test banner printing."""
        print_banner()

        captured = capsys.readouterr()
        assert "apollonia" in captured.out
        assert "populator" in captured.out

    @patch("populator.populator.asyncio.run")
    @patch("populator.populator.setup_logging")
    @patch("populator.populator.print_banner")
    @patch("populator.populator.AMQP_CONNECTION", "amqp://test:test@localhost")
    def test_main(self, mock_banner: Mock, mock_logging: Mock, mock_run: Mock) -> None:
        """Test main function."""
        main()

        mock_logging.assert_called_once()
        mock_banner.assert_called_once()
        mock_run.assert_called_once()

    @patch("populator.populator.asyncio.run")
    @patch("populator.populator.logger")
    @patch("populator.populator.AMQP_CONNECTION", None)
    def test_main_no_amqp_connection(self, mock_logger: Mock, mock_run: Mock) -> None:
        """Test main function without AMQP connection."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_once()
        mock_run.assert_not_called()

    @patch("populator.populator.logger")
    @patch("populator.populator.NEO4J_PASSWORD", "password")
    def test_main_default_password_warning(self, mock_logger: Mock) -> None:
        """Test warning for default Neo4j password."""
        with patch("populator.populator.asyncio.run"):
            main()

        mock_logger.warning.assert_called_once()
        assert "default Neo4j password" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    @patch("populator.populator.Populator")
    async def test_async_main(self, mock_populator_class: Mock) -> None:
        """Test async_main function."""
        from populator.populator import async_main

        # Setup mock populator
        mock_populator = AsyncMock()
        mock_populator_class.return_value.__aenter__.return_value = mock_populator

        await async_main()

        mock_populator_class.assert_called_once()
        mock_populator.consume.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("populator.populator.signal.signal")
    @patch("populator.populator.Populator")
    async def test_signal_handler(self, mock_populator_class: Mock, mock_signal: Mock) -> None:
        """Test signal handler setup and execution."""
        from populator.populator import async_main

        # Capture the signal handler
        signal_handler = None

        def capture_handler(sig, handler):
            nonlocal signal_handler
            if sig == 2:  # SIGINT
                signal_handler = handler

        mock_signal.side_effect = capture_handler

        # Setup mock populator
        mock_populator = AsyncMock()
        mock_populator_class.return_value.__aenter__.return_value = mock_populator

        # Make consume return immediately
        mock_populator.consume.return_value = None

        await async_main()

        # Verify signal handlers were registered
        assert mock_signal.call_count == 2  # SIGINT and SIGTERM

        # Test the signal handler
        if signal_handler:
            signal_handler(2, None)
            mock_populator.stop.assert_called_once()
