"""Tests for the Ingestor service."""
# mypy: disable-error-code="name-defined"

from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ingestor.ingestor import Ingestor, main, print_banner, setup_logging


class TestIngestor:
    """Test cases for the Ingestor class."""

    def test_init(self) -> None:
        """Test Ingestor initialization."""
        ingestor = Ingestor()

        assert ingestor.amqp_connection is None
        assert ingestor.amqp_channel is None
        assert ingestor._running is True
        assert ingestor.amqp_properties.content_encoding == "application/json"
        assert ingestor.amqp_properties.delivery_mode == 2

    @patch("ingestor.ingestor.BlockingConnection")
    @patch("ingestor.ingestor.URLParameters")
    def test_enter(self, mock_url_params: Mock, mock_connection: Mock) -> None:
        """Test context manager enter."""
        # Setup mocks
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel

        ingestor = Ingestor()
        result = ingestor.__enter__()

        # Verify connection setup
        mock_url_params.assert_called_once()
        mock_connection.assert_called_once()
        assert ingestor.amqp_connection is not None
        assert ingestor.amqp_channel == mock_channel
        assert result == ingestor

        # Verify exchange declaration
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="apollonia",
            exchange_type="fanout",
            durable=True,
            auto_delete=False,
        )

    def test_exit(self) -> None:
        """Test context manager exit."""
        ingestor = Ingestor()
        mock_connection = Mock()
        mock_connection.is_closed = False
        ingestor.amqp_connection = mock_connection

        ingestor.__exit__(None, None, None)

        mock_connection.close.assert_called_once()

    def test_exit_no_connection(self) -> None:
        """Test exit when no connection exists."""
        ingestor = Ingestor()
        # Should not raise
        ingestor.__exit__(None, None, None)

    def test_stop(self) -> None:
        """Test stop method."""
        ingestor = Ingestor()
        assert ingestor._running is True

        ingestor.stop()

        assert ingestor._running is False

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.Observer")
    @patch("ingestor.ingestor.Path")
    async def test_ingest_basic(self, mock_path_class: Mock, mock_observer_class: Mock) -> None:
        """Test basic ingest functionality."""
        # Setup mocks
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        mock_observer.start = Mock()
        mock_observer.stop = Mock()
        mock_observer.join = Mock()

        # Setup path mock
        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.mkdir = Mock()

        # Mock channel
        mock_channel = Mock()

        # Capture the event handler
        event_handler = None

        def capture_handler(handler: Any, path: Any, recursive: Any = False) -> None:  # noqa: ARG001
            nonlocal event_handler
            event_handler = handler

        mock_observer.schedule = Mock(side_effect=capture_handler)

        # Mock prospector
        with patch("ingestor.ingestor.Prospector") as mock_prospector_class:
            mock_prospector = AsyncMock()
            mock_prospector.prospect.return_value = {
                "file_path": "/data/test.txt",
                "sha256_hash": "abc123",
                "xxh128_hash": "def456",
            }
            mock_prospector_class.return_value = mock_prospector

            # Run ingest
            ingestor = Ingestor()
            ingestor.amqp_channel = mock_channel

            # Start ingest in background
            ingest_task = asyncio.create_task(ingestor.ingest())

            # Wait for setup
            await asyncio.sleep(0.1)

            # Simulate file event
            if event_handler:
                mock_event = Mock()
                mock_event.is_directory = False
                mock_event.src_path = "/data/test.txt"
                event_handler.on_created(mock_event)

                # Wait for processing
                await asyncio.sleep(0.1)

            # Stop ingestor
            ingestor.stop()
            await ingest_task

        # Verify
        # Path is called with both /data (for mkdir) and /data/test.txt (for Prospector)
        mock_path_class.assert_any_call("/data")
        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_observer.schedule.assert_called_once()
        # Since Path is mocked, check it was called with the test file path
        mock_path_class.assert_any_call("/data/test.txt")
        mock_prospector_class.assert_called_once_with(mock_path)
        mock_channel.basic_publish.assert_called_once()

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.Observer")
    @patch("ingestor.ingestor.Path")
    async def test_ingest_error_handling(
        self, mock_path_class: Mock, mock_observer_class: Mock
    ) -> None:
        """Test error handling during ingest."""
        # Setup mocks
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        mock_observer.start = Mock()
        mock_observer.stop = Mock()
        mock_observer.join = Mock()

        # Setup path mock
        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.mkdir = Mock()

        # Capture the event handler
        event_handler = None

        def capture_handler(handler: Any, path: Any, recursive: Any = False) -> None:  # noqa: ARG001
            nonlocal event_handler
            event_handler = handler

        mock_observer.schedule = Mock(side_effect=capture_handler)

        # Mock prospector to raise an exception
        with patch("ingestor.ingestor.Prospector") as mock_prospector_class:
            mock_prospector = AsyncMock()
            mock_prospector.prospect.side_effect = Exception("Test error")
            mock_prospector_class.return_value = mock_prospector

            # Run ingest - should not raise
            ingestor = Ingestor()
            ingestor.amqp_channel = Mock()

            # Start ingest in background
            ingest_task = asyncio.create_task(ingestor.ingest())

            # Wait for setup
            await asyncio.sleep(0.1)

            # Simulate file event that will cause error
            if event_handler:
                mock_event = Mock()
                mock_event.is_directory = False
                mock_event.src_path = "/data/error.txt"
                event_handler.on_created(mock_event)

                # Wait for processing
                await asyncio.sleep(0.1)

            # Stop ingestor
            ingestor.stop()
            await ingest_task

        # Verify error was handled
        mock_prospector_class.assert_called_once()
        # Channel publish should not be called due to error
        ingestor.amqp_channel.basic_publish.assert_not_called()

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.Observer")
    @patch("ingestor.ingestor.Path")
    async def test_ingest_stop_signal(
        self, mock_path_class: Mock, mock_observer_class: Mock
    ) -> None:
        """Test that ingest stops when _running is False."""
        # Setup mocks
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        mock_observer.start = Mock()
        mock_observer.stop = Mock()
        mock_observer.join = Mock()
        mock_observer.schedule = Mock()

        # Setup path mock
        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.mkdir = Mock()

        ingestor = Ingestor()
        ingestor.amqp_channel = Mock()

        # Stop the ingestor after a short delay
        async def stop_after_delay() -> None:
            await asyncio.sleep(0.1)
            ingestor.stop()

        # Run both coroutines
        await asyncio.gather(ingestor.ingest(), stop_after_delay())

        # Verify it stopped
        assert ingestor._running is False
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()


class TestMainFunctions:
    """Test main functions and entry points."""

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("ingestor.ingestor.logging.basicConfig") as mock_config:
            setup_logging()

            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args["level"] == logging.INFO
            assert "%(asctime)s" in call_args["format"]

    def test_print_banner(self, capsys: pytest.CaptureFixture) -> None:
        """Test banner printing."""
        print_banner()

        captured = capsys.readouterr()
        # The banner uses unicode characters, check for some parts
        assert "_" in captured.out  # ASCII art contains underscores
        assert len(captured.out) > 0  # Banner was printed

    @patch("ingestor.ingestor.asyncio.run")
    @patch("ingestor.ingestor.setup_logging")
    @patch("ingestor.ingestor.print_banner")
    @patch("ingestor.ingestor.AMQP_CONNECTION", "amqp://test:test@localhost")
    def test_main(self, mock_banner: Mock, mock_logging: Mock, mock_run: Mock) -> None:
        """Test main function."""
        main()

        mock_logging.assert_called_once()
        mock_banner.assert_called_once()
        mock_run.assert_called_once()

    @patch("ingestor.ingestor.asyncio.run")
    @patch("ingestor.ingestor.logger")
    @patch("ingestor.ingestor.AMQP_CONNECTION", None)
    def test_main_no_amqp_connection(self, mock_logger: Mock, mock_run: Mock) -> None:
        """Test main function without AMQP connection."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_once()
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.Ingestor")
    async def test_async_main(self, mock_ingestor_class: Mock) -> None:
        """Test async_main function."""
        from ingestor.ingestor import async_main

        # Setup mock ingestor instance
        mock_ingestor_instance = AsyncMock()
        mock_ingestor_instance.ingest = AsyncMock()

        # Mock the context manager behavior
        mock_ingestor_class.return_value.__enter__.return_value = mock_ingestor_instance
        mock_ingestor_class.return_value.__exit__.return_value = None

        await async_main()

        mock_ingestor_class.assert_called_once()
        mock_ingestor_instance.ingest.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.Ingestor")
    @patch("ingestor.ingestor.logger")
    async def test_async_main_error(self, mock_logger: Mock, mock_ingestor_class: Mock) -> None:
        """Test async_main with error."""
        from ingestor.ingestor import async_main

        # Setup mock to raise exception
        mock_ingestor_class.side_effect = Exception("Test error")

        with pytest.raises(SystemExit) as exc_info:
            await async_main()

        assert exc_info.value.code == 1
        mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    @patch("ingestor.ingestor.signal.signal")
    @patch("ingestor.ingestor.Ingestor")
    async def test_signal_handler(self, mock_ingestor_class: Mock, mock_signal: Mock) -> None:
        """Test signal handler setup and execution."""
        from ingestor.ingestor import async_main

        # Capture the signal handler
        signal_handler = None

        def capture_handler(sig: int, handler: Any) -> None:
            nonlocal signal_handler
            if sig == 2:  # SIGINT
                signal_handler = handler

        mock_signal.side_effect = capture_handler

        # Setup mock ingestor instance
        mock_ingestor_instance = AsyncMock()
        mock_ingestor_instance.ingest = AsyncMock()
        mock_ingestor_instance.stop = Mock()

        # Mock the context manager behavior
        mock_ingestor_class.return_value.__enter__.return_value = mock_ingestor_instance
        mock_ingestor_class.return_value.__exit__.return_value = None

        await async_main()

        # Verify signal handlers were registered
        assert mock_signal.call_count == 2  # SIGINT and SIGTERM

        # Test the signal handler
        if signal_handler:
            signal_handler(2, None)
            mock_ingestor_instance.stop.assert_called_once()
