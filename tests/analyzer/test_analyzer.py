"""Unit tests for the ML analyzer service."""

import asyncio
import logging
import signal
from typing import Any
from unittest.mock import AsyncMock, patch

import orjson
import pytest
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection


class TestMLAnalyzer:
    """Test cases for the MLAnalyzer class."""

    @pytest.fixture
    def mock_amqp_connection(self) -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
        """Create a mock AMQP connection."""
        connection = AsyncMock(spec=AbstractRobustConnection)
        channel = AsyncMock()
        exchange = AsyncMock()
        queue = AsyncMock()

        # Set up the mock chain
        connection.channel.return_value = channel
        channel.declare_exchange.return_value = exchange
        channel.declare_queue.return_value = queue
        queue.bind = AsyncMock()

        return connection, channel, exchange, queue

    @pytest.fixture
    def mock_message(self) -> AsyncMock:
        """Create a mock AMQP message."""
        message = AsyncMock(spec=AbstractIncomingMessage)
        message.body = orjson.dumps(
            {
                "file_path": "/test/audio.mp3",
                "media_metadata": {"media_type": "audio"},
                "sha256_hash": "abc123",
                "xxh128_hash": "def456",
                "size": 1024,
            }
        )

        # Set up process context manager
        process_mock = AsyncMock()
        process_mock.__aenter__ = AsyncMock(return_value=None)
        process_mock.__aexit__ = AsyncMock(return_value=None)
        message.process.return_value = process_mock

        return message

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self) -> None:
        """Test that MLAnalyzer can be initialized."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            analyzer = MLAnalyzer()
            assert analyzer.amqp_connection is None
            assert analyzer.amqp_channel is None
            assert analyzer._running is True
            assert analyzer.model_manager is not None
            assert analyzer.audio_processor is not None
            assert analyzer.video_processor is not None

    @pytest.mark.asyncio
    async def test_analyzer_context_manager_enter(self) -> None:
        """Test __aenter__ sets up connections properly."""
        with (
            patch("analyzer.analyzer.connect_robust") as mock_connect,
            patch("analyzer.analyzer.ModelManager") as mock_model_manager,
        ):
            from analyzer.analyzer import (
                AMQP_CONNECTION,
                AMQP_EXCHANGE_IN,
                AMQP_QUEUE,
                MLAnalyzer,
            )

            # Set up mocks
            amqp_connection = AsyncMock()
            amqp_channel = AsyncMock()
            queue = AsyncMock()

            mock_connect.return_value = amqp_connection
            amqp_connection.channel.return_value = amqp_channel
            amqp_channel.declare_exchange.return_value = AsyncMock()
            amqp_channel.declare_queue.return_value = queue
            queue.bind = AsyncMock()

            # Mock model manager
            model_manager = AsyncMock()
            mock_model_manager.return_value = model_manager
            model_manager.initialize = AsyncMock()

            # Create analyzer
            analyzer = MLAnalyzer()
            result = await analyzer.__aenter__()

            # Verify
            assert result is analyzer
            mock_connect.assert_called_once_with(AMQP_CONNECTION)
            assert analyzer.amqp_connection is amqp_connection
            assert analyzer.amqp_channel is amqp_channel

            # Verify exchanges were declared
            assert amqp_channel.declare_exchange.call_count == 2

            # Verify queue was declared and bound
            amqp_channel.declare_queue.assert_called_once_with(AMQP_QUEUE, durable=True)
            queue.bind.assert_called_once_with(AMQP_EXCHANGE_IN, routing_key="media.#")

            # Verify model manager was initialized
            model_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyzer_context_manager_exit(self) -> None:
        """Test __aexit__ closes connections properly."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            # Create analyzer with mock connection
            analyzer = MLAnalyzer()
            analyzer.amqp_connection = AsyncMock()

            # Test exit
            await analyzer.__aexit__(None, None, None)

            # Verify connection was closed
            analyzer.amqp_connection.close.assert_called_once()

    def test_stop(self) -> None:
        """Test stop method sets _running to False."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            analyzer = MLAnalyzer()
            assert analyzer._running is True
            analyzer.stop()
            assert analyzer._running is False

    @pytest.mark.asyncio
    async def test_process_message_audio_success(self, mock_message: AsyncMock) -> None:
        """Test successful audio message processing."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor") as mock_audio_processor_class,
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            # Set up mocks
            mock_audio_processor = AsyncMock()
            mock_audio_processor.process.return_value = {"tempo": 120, "key": "C"}
            mock_audio_processor_class.return_value = mock_audio_processor

            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            mock_channel.get_exchange.return_value = mock_exchange

            # Create analyzer
            analyzer = MLAnalyzer()
            analyzer.amqp_channel = mock_channel

            # Process message
            await analyzer.process_message(mock_message)

            # Verify message was processed
            mock_message.process.assert_called_once()

            # Verify audio processor was called
            mock_audio_processor.process.assert_called_once()

            # Verify enriched data was published
            mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_video_success(self, mock_message: AsyncMock) -> None:
        """Test successful video message processing."""
        # Modify message for video
        video_data = orjson.loads(mock_message.body)
        video_data["media_metadata"]["media_type"] = "video"
        video_data["file_path"] = "/test/video.mp4"
        mock_message.body = orjson.dumps(video_data)

        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor") as mock_video_processor_class,
        ):
            from analyzer.analyzer import MLAnalyzer

            # Set up mocks
            mock_video_processor = AsyncMock()
            mock_video_processor.process.return_value = {"duration": 300, "fps": 30}
            mock_video_processor_class.return_value = mock_video_processor

            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            mock_channel.get_exchange.return_value = mock_exchange

            # Create analyzer
            analyzer = MLAnalyzer()
            analyzer.amqp_channel = mock_channel

            # Process message
            await analyzer.process_message(mock_message)

            # Verify video processor was called
            mock_video_processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_unsupported_type(self, mock_message: AsyncMock) -> None:
        """Test processing message with unsupported media type."""
        # Modify message for unsupported type
        unsupported_data = orjson.loads(mock_message.body)
        unsupported_data["media_metadata"]["media_type"] = "document"
        mock_message.body = orjson.dumps(unsupported_data)

        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            # Create analyzer
            analyzer = MLAnalyzer()

            # Process message - should not raise exception
            await analyzer.process_message(mock_message)

            # Verify message was processed (context manager entered)
            mock_message.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, mock_message: AsyncMock) -> None:
        """Test message processing handles errors gracefully."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
            patch("analyzer.analyzer.orjson.loads", side_effect=Exception("Parse error")),
        ):
            from analyzer.analyzer import MLAnalyzer

            analyzer = MLAnalyzer()

            # Process message - should not raise exception
            await analyzer.process_message(mock_message)

            # Verify message was processed (context manager entered)
            mock_message.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_consume_no_channel(self) -> None:
        """Test consume raises error when no channel."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import MLAnalyzer

            analyzer = MLAnalyzer()
            analyzer.amqp_channel = None

            with pytest.raises(RuntimeError, match="AMQP channel not initialized"):
                await analyzer.consume()

    @pytest.mark.asyncio
    async def test_consume_setup_and_iteration(
        self, mock_amqp_connection: tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]
    ) -> None:
        """Test consume processes messages."""
        with (
            patch("analyzer.analyzer.ModelManager"),
            patch("analyzer.analyzer.AudioProcessor"),
            patch("analyzer.analyzer.VideoProcessor"),
        ):
            from analyzer.analyzer import AMQP_QUEUE, MLAnalyzer

            connection, channel, exchange, queue = mock_amqp_connection

            # Set up mock messages
            mock_msg1 = AsyncMock()
            mock_msg2 = AsyncMock()
            messages = [mock_msg1, mock_msg2]

            # Create async iterator for queue
            async def message_iterator() -> Any:
                for msg in messages:
                    if not analyzer._running:
                        return
                    yield msg

            # Mock the queue iterator properly
            class MockAsyncIterator:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

                async def __aiter__(self):
                    for msg in messages:
                        if not analyzer._running:
                            break
                        yield msg

            def mock_iterator():
                return MockAsyncIterator()

            queue.iterator = mock_iterator
            channel.get_queue.return_value = queue

            # Create analyzer
            analyzer = MLAnalyzer()
            analyzer.amqp_channel = channel
            analyzer.process_message = AsyncMock()

            # Stop after processing messages
            async def stop_after_messages() -> None:
                await asyncio.sleep(0.1)
                analyzer.stop()

            task = asyncio.create_task(stop_after_messages())
            await analyzer.consume()
            await task

            # Verify queue was retrieved
            channel.get_queue.assert_called_once_with(AMQP_QUEUE)

            # Verify messages were processed
            assert analyzer.process_message.call_count == 2
            analyzer.process_message.assert_any_call(mock_msg1)
            analyzer.process_message.assert_any_call(mock_msg2)

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("analyzer.analyzer.logging.basicConfig") as mock_config:
            from analyzer.analyzer import setup_logging

            setup_logging()

            mock_config.assert_called_once()
            args = mock_config.call_args
            assert args.kwargs["level"] == logging.INFO
            assert "%(asctime)s" in args.kwargs["format"]
            assert len(args.kwargs["handlers"]) == 1

    def test_print_banner(self, capsys: Any) -> None:
        """Test banner printing."""
        from analyzer.analyzer import print_banner

        print_banner()

        captured = capsys.readouterr()
        assert "ml" in captured.out.lower()
        assert "analysis" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_async_main_signal_handling(self) -> None:
        """Test async_main sets up signal handlers correctly."""
        with (
            patch("analyzer.analyzer.signal.signal") as mock_signal,
            patch("analyzer.analyzer.MLAnalyzer") as mock_analyzer_class,
        ):
            from analyzer.analyzer import async_main

            # Set up mock
            mock_analyzer = AsyncMock()
            mock_analyzer_class.return_value.__aenter__.return_value = mock_analyzer
            mock_analyzer_class.return_value.__aexit__.return_value = None

            # Run
            await async_main()

            # Verify signal handlers were registered
            assert mock_signal.call_count >= 2
            signal_calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in signal_calls]
            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered

    @pytest.mark.asyncio
    async def test_async_main_keyboard_interrupt(self) -> None:
        """Test async_main handles KeyboardInterrupt gracefully."""
        with patch("analyzer.analyzer.MLAnalyzer") as mock_analyzer_class:
            from analyzer.analyzer import async_main

            # Make consume raise KeyboardInterrupt
            mock_analyzer = AsyncMock()
            mock_analyzer.consume.side_effect = KeyboardInterrupt()
            mock_analyzer_class.return_value.__aenter__.return_value = mock_analyzer
            mock_analyzer_class.return_value.__aexit__.return_value = None

            # Should not raise exception
            await async_main()

    @pytest.mark.asyncio
    async def test_async_main_fatal_error(self) -> None:
        """Test async_main handles fatal errors."""
        with (
            patch("analyzer.analyzer.MLAnalyzer") as mock_analyzer_class,
            patch("analyzer.analyzer.sys.exit") as mock_exit,
        ):
            from analyzer.analyzer import async_main

            # Make consume raise exception
            mock_analyzer = AsyncMock()
            mock_analyzer.consume.side_effect = Exception("Fatal error")
            mock_analyzer_class.return_value.__aenter__.return_value = mock_analyzer
            mock_analyzer_class.return_value.__aexit__.return_value = None

            # Run
            await async_main()

            # Verify exit was called
            mock_exit.assert_called_once_with(1)

    def test_main_missing_amqp_connection(self) -> None:
        """Test main exits when AMQP connection string is missing."""
        with (
            patch("analyzer.analyzer.setup_logging"),
            patch("analyzer.analyzer.print_banner"),
            patch("analyzer.analyzer.AMQP_CONNECTION", ""),
            patch("analyzer.analyzer.sys.exit") as mock_exit,
        ):
            from analyzer.analyzer import main

            main()

            assert mock_exit.called

    def test_main_successful_run(self) -> None:
        """Test main runs successfully with proper configuration."""
        with (
            patch("analyzer.analyzer.setup_logging"),
            patch("analyzer.analyzer.print_banner"),
            patch("analyzer.analyzer.AMQP_CONNECTION", "amqp://test:test@localhost:5672/"),
            patch("analyzer.analyzer.asyncio.run") as mock_run,
        ):
            from analyzer.analyzer import main

            main()

            mock_run.assert_called_once()
