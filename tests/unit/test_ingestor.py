"""Unit tests for the ingestor service."""

import logging
import signal
import sys
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import orjson
import pytest
from pika import BlockingConnection
from pika.spec import DeliveryMode


class TestIngestor:
    """Test cases for the Ingestor class."""

    @pytest.fixture
    def mock_amqp_connection(self) -> Mock:
        """Create a mock AMQP connection."""
        connection = Mock(spec=BlockingConnection)
        connection.is_closed = False
        return connection

    @pytest.fixture
    def mock_amqp_channel(self) -> Mock:
        """Create a mock AMQP channel."""
        channel = Mock()
        channel.exchange_declare = Mock()
        channel.basic_publish = Mock()
        return channel

    @pytest.fixture
    def mock_inotify(self) -> Generator[tuple[Mock, AsyncMock], None, None]:
        """Create a mock Inotify instance."""
        with patch("asyncinotify.Inotify") as mock:
            inotify_instance = AsyncMock()
            inotify_instance.add_watch = Mock()
            mock.return_value.__aenter__.return_value = inotify_instance
            yield mock, inotify_instance

    @pytest.fixture
    def mock_prospector(self) -> Generator[tuple[Mock, Mock], None, None]:
        """Create a mock Prospector."""
        with patch("ingestor.ingestor.Prospector") as mock:
            prospector_instance = Mock()
            prospector_instance.prospect = AsyncMock(
                return_value={
                    "file_path": "/test/file.txt",
                    "sha256_hash": "abc123",
                    "xxh128_hash": "def456",
                    "size": 1024,
                    "event_type": "IN_CREATE",
                    "neighbors": [],
                }
            )
            mock.return_value = prospector_instance
            yield mock, prospector_instance

    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    def test_ingestor_initialization(self) -> None:
        """Test that Ingestor can be initialized."""
        # Mock all the dependencies before importing
        with (
            patch("ingestor.ingestor.BlockingConnection"),
            patch("asyncinotify.Inotify"),
            patch("asyncinotify.Mask"),
        ):
            from ingestor.ingestor import Ingestor

            ingestor = Ingestor()
            assert ingestor.amqp_connection is None
            assert ingestor.amqp_channel is None
            assert ingestor._running is True
            assert ingestor.amqp_properties.delivery_mode == DeliveryMode.Persistent.value
            assert ingestor.amqp_properties.content_encoding == "application/json"

    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    def test_ingestor_context_manager_enter(
        self, mock_amqp_connection: Mock, mock_amqp_channel: Mock
    ) -> None:
        """Test __enter__ sets up AMQP connection properly."""
        with (
            patch("ingestor.ingestor.BlockingConnection") as mock_conn_class,
            patch("ingestor.ingestor.URLParameters") as mock_url_params,
            patch("asyncinotify.Inotify"),
            patch("asyncinotify.Mask"),
        ):
            # Set up mocks
            mock_conn_class.return_value = mock_amqp_connection
            mock_amqp_connection.channel.return_value = mock_amqp_channel

            from ingestor.ingestor import AMQP_CONNECTION, AMQP_EXCHANGE, Ingestor

            ingestor = Ingestor()
            result = ingestor.__enter__()

            # Verify
            assert result is ingestor
            mock_url_params.assert_called_once_with(AMQP_CONNECTION)
            mock_conn_class.assert_called_once()
            mock_amqp_connection.channel.assert_called_once()
            mock_amqp_channel.exchange_declare.assert_called_once_with(
                exchange=AMQP_EXCHANGE,
                exchange_type="fanout",
                durable=True,
                auto_delete=False,
            )
            assert ingestor.amqp_connection is mock_amqp_connection
            assert ingestor.amqp_channel is mock_amqp_channel

    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    def test_ingestor_context_manager_exit(self, mock_amqp_connection: Mock) -> None:
        """Test __exit__ closes AMQP connection properly."""
        with (
            patch("asyncinotify.Inotify"),
            patch("asyncinotify.Mask"),
        ):
            from ingestor.ingestor import Ingestor

            ingestor = Ingestor()
            ingestor.amqp_connection = mock_amqp_connection

            # Test normal exit
            ingestor.__exit__(None, None, None)
            mock_amqp_connection.close.assert_called_once()

            # Test exit when connection already closed
            mock_amqp_connection.reset_mock()
            mock_amqp_connection.is_closed = True
            ingestor.__exit__(None, None, None)
            mock_amqp_connection.close.assert_not_called()

    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    def test_stop(self) -> None:
        """Test stop method sets _running to False."""
        with (
            patch("asyncinotify.Inotify"),
            patch("asyncinotify.Mask"),
        ):
            from ingestor.ingestor import Ingestor

            ingestor = Ingestor()
            assert ingestor._running is True
            ingestor.stop()
            assert ingestor._running is False

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    async def test_ingest_creates_directory(
        self,
        mock_inotify: tuple[Mock, AsyncMock],
        mock_prospector: tuple[Mock, Mock],  # noqa: ARG002
    ) -> None:
        """Test ingest creates data directory if it doesn't exist."""
        with (
            patch("ingestor.ingestor.Path") as mock_path_class,
            patch("asyncinotify.Mask"),
        ):
            from ingestor.ingestor import DATA_DIRECTORY, Ingestor

            # Set up mock
            mock_path = Mock()
            mock_path_class.return_value = mock_path
            _, inotify_instance = mock_inotify

            # Make inotify return no events (empty async iterator)
            async def empty_generator() -> AsyncGenerator[None, None]:
                return
                yield  # Make it a generator

            inotify_instance.__aiter__.return_value = empty_generator()

            ingestor = Ingestor()
            ingestor._running = False  # Stop immediately
            await ingestor.ingest()

            # Verify
            mock_path_class.assert_called_once_with(DATA_DIRECTORY)
            mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    async def test_ingest_processes_events(
        self,
        mock_inotify: tuple[Mock, AsyncMock],
        mock_prospector: tuple[Mock, Mock],
        mock_amqp_channel: Mock,
    ) -> None:
        """Test ingest processes file events and publishes to AMQP."""
        with patch("asyncinotify.Mask"):
            from ingestor.ingestor import AMQP_EXCHANGE, ROUTING_KEY, Ingestor

            # Set up mocks
            _, inotify_instance = mock_inotify
            _, prospector_instance = mock_prospector

            # Create mock events
            mock_event1 = Mock()
            mock_event1.path = "/test/file1.txt"
            mock_event1.mask = "IN_CREATE"

            mock_event2 = Mock()
            mock_event2.path = "/test/file2.txt"
            mock_event2.mask = "IN_MOVED_TO"

            # Make inotify return events
            events = [mock_event1, mock_event2]
            event_index = 0

            async def event_generator() -> AsyncGenerator[Mock, None]:
                nonlocal event_index
                for event in events:
                    if event_index >= len(events) or not ingestor._running:
                        return
                    yield event
                    event_index += 1

            inotify_instance.__aiter__.return_value = event_generator()

            # Create ingestor
            ingestor = Ingestor()
            ingestor.amqp_channel = mock_amqp_channel

            # Run ingest in a task and stop after processing events
            async def run_and_stop() -> None:
                await asyncio.sleep(0.1)  # Let it process events
                ingestor.stop()

            import asyncio

            task = asyncio.create_task(run_and_stop())
            await ingestor.ingest()
            await task

            # Verify prospector was called for each event
            _, prospector_instance = mock_prospector
            assert mock_prospector[0].call_count == 2
            mock_prospector[0].assert_any_call("/test/file1.txt")
            mock_prospector[0].assert_any_call("/test/file2.txt")

            # Verify AMQP publishes
            assert mock_amqp_channel.basic_publish.call_count == 2

            # Check first publish
            first_call = mock_amqp_channel.basic_publish.call_args_list[0]
            assert first_call.kwargs["exchange"] == AMQP_EXCHANGE
            assert first_call.kwargs["routing_key"] == ROUTING_KEY
            assert orjson.loads(first_call.kwargs["body"])["file_path"] == "/test/file.txt"

            # Check second publish
            second_call = mock_amqp_channel.basic_publish.call_args_list[1]
            assert second_call.kwargs["exchange"] == AMQP_EXCHANGE
            assert second_call.kwargs["routing_key"] == ROUTING_KEY

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    async def test_ingest_handles_processing_errors(
        self,
        mock_inotify: tuple[Mock, AsyncMock],
        mock_prospector: tuple[Mock, Mock],
        mock_amqp_channel: Mock,
    ) -> None:
        """Test ingest handles errors during event processing gracefully."""
        with patch("asyncinotify.Mask"):
            from ingestor.ingestor import Ingestor

            # Set up mocks
            _, inotify_instance = mock_inotify
            _, prospector_instance = mock_prospector

            # Make prospector raise an exception
            prospector_instance.prospect.side_effect = Exception("Processing error")

            # Create mock event
            mock_event = Mock()
            mock_event.path = "/test/error.txt"
            mock_event.mask = "IN_CREATE"

            async def event_generator() -> AsyncGenerator[Mock, None]:
                yield mock_event
                ingestor.stop()

            inotify_instance.__aiter__.return_value = event_generator()

            # Create ingestor
            ingestor = Ingestor()
            ingestor.amqp_channel = mock_amqp_channel

            # Run ingest - should not raise exception
            await ingestor.ingest()

            # Verify prospector was called
            mock_prospector[0].assert_called_once_with("/test/error.txt")

            # Verify no AMQP publish due to error
            mock_amqp_channel.basic_publish.assert_not_called()

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("logging.basicConfig") as mock_config:
            # Mock asyncinotify before importing ingestor on macOS
            if sys.platform == "darwin":
                with patch.dict("sys.modules", {"asyncinotify": Mock()}):
                    from ingestor.ingestor import setup_logging

                    setup_logging()
            else:
                from ingestor.ingestor import setup_logging

                setup_logging()

            mock_config.assert_called_once()
            args = mock_config.call_args
            assert args.kwargs["level"] == logging.INFO
            assert "%(asctime)s" in args.kwargs["format"]
            assert len(args.kwargs["handlers"]) == 1

    def test_print_banner(self, capsys: Any) -> None:
        """Test banner printing."""
        # Mock asyncinotify before importing ingestor on macOS
        if sys.platform == "darwin":
            with patch.dict("sys.modules", {"asyncinotify": Mock()}):
                from ingestor.ingestor import print_banner
        else:
            from ingestor.ingestor import print_banner

        print_banner()

        captured = capsys.readouterr()
        # The banner is ASCII art, just verify it prints something
        assert len(captured.out) > 0
        assert "___" in captured.out  # Part of the ASCII art

    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")
    async def test_async_main_signal_handling(self) -> None:
        """Test async_main sets up signal handlers correctly."""
        with (
            patch("ingestor.ingestor.signal.signal") as mock_signal,
            patch("ingestor.ingestor.Ingestor") as mock_ingestor_class,
            patch("asyncinotify.Inotify"),
            patch("asyncinotify.Mask"),
        ):
            from ingestor.ingestor import async_main

            # Set up mock
            mock_ingestor = Mock()
            mock_ingestor.ingest = AsyncMock()
            mock_ingestor_class.return_value.__enter__.return_value = mock_ingestor
            mock_ingestor_class.return_value.__exit__.return_value = None

            # Run
            await async_main()

            # Verify signal handlers were registered
            assert mock_signal.call_count >= 2
            signal_calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in signal_calls]
            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered

    def test_main_missing_amqp_connection(self) -> None:
        """Test main exits when AMQP connection string is missing."""
        # Mock asyncinotify before importing ingestor on macOS
        if sys.platform == "darwin":
            with (
                patch.dict("sys.modules", {"asyncinotify": Mock()}),
                patch("ingestor.ingestor.setup_logging"),
                patch("ingestor.ingestor.print_banner"),
                patch("ingestor.ingestor.AMQP_CONNECTION", ""),
                patch("ingestor.ingestor.sys.exit") as mock_exit,
                patch("ingestor.ingestor.asyncio.run"),
            ):
                from ingestor.ingestor import main

                main()
                mock_exit.assert_called_once_with(1)
        else:
            with (
                patch("ingestor.ingestor.setup_logging"),
                patch("ingestor.ingestor.print_banner"),
                patch("ingestor.ingestor.AMQP_CONNECTION", ""),
                patch("ingestor.ingestor.sys.exit") as mock_exit,
                patch("ingestor.ingestor.asyncio.run"),
            ):
                from ingestor.ingestor import main

                main()
                mock_exit.assert_called_once_with(1)

    def test_main_successful_run(self) -> None:
        """Test main runs successfully with proper configuration."""
        # Mock asyncinotify before importing ingestor on macOS
        if sys.platform == "darwin":
            with (
                patch.dict("sys.modules", {"asyncinotify": Mock()}),
                patch("ingestor.ingestor.setup_logging"),
                patch("ingestor.ingestor.print_banner"),
                patch("ingestor.ingestor.AMQP_CONNECTION", "amqp://test:test@localhost:5672/"),
                patch("ingestor.ingestor.asyncio.run") as mock_run,
            ):
                from ingestor.ingestor import main

                main()
                mock_run.assert_called_once()
        else:
            with (
                patch("ingestor.ingestor.setup_logging"),
                patch("ingestor.ingestor.print_banner"),
                patch("ingestor.ingestor.AMQP_CONNECTION", "amqp://test:test@localhost:5672/"),
                patch("ingestor.ingestor.asyncio.run") as mock_run,
            ):
                from ingestor.ingestor import main

                main()
                mock_run.assert_called_once()
