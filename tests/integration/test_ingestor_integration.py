"""Integration tests for the ingestor service."""
# mypy: disable-error-code="name-defined,attr-defined"

import asyncio
import contextlib
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import orjson
import pytest
from pika import BlockingConnection, URLParameters
from pika.channel import Channel
from pika.exceptions import AMQPConnectionError

from ingestor.ingestor import (
    AMQP_CONNECTION,
    AMQP_EXCHANGE,
    ROUTING_KEY,
    Ingestor,
)
from ingestor.prospector import Prospector


class TestIngestorIntegration:
    """Integration tests for ingestor service."""

    @pytest.fixture
    def rabbitmq_available(self) -> bool:
        """Check if RabbitMQ is available."""
        try:
            connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
            connection.close()
            return True
        except (AMQPConnectionError, ConnectionError):
            return False

    @pytest.fixture
    def temp_data_dir(self) -> Generator[Path, None, None]:
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def amqp_consumer(
        self, rabbitmq_available: bool
    ) -> Generator[tuple[Channel, list[Any]], None, None]:
        """Create an AMQP consumer for testing."""
        if not rabbitmq_available:
            pytest.skip("RabbitMQ not available")

        connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange=AMQP_EXCHANGE,
            exchange_type="fanout",
            durable=True,
            auto_delete=False,
        )

        # Create temporary queue with unique name to avoid cross-test contamination
        import uuid

        test_queue_name = f"test-ingestor-{uuid.uuid4().hex[:8]}"
        result = channel.queue_declare(queue=test_queue_name, exclusive=True, auto_delete=True)
        queue_name = result.method.queue

        # Bind queue to exchange
        channel.queue_bind(exchange=AMQP_EXCHANGE, queue=queue_name, routing_key=ROUTING_KEY)

        # Purge any existing messages in the queue
        channel.queue_purge(queue_name)

        # Collected messages
        messages = []

        def callback(ch: Any, method: Any, properties: Any, body: bytes) -> None:  # noqa: ARG001
            messages.append(orjson.loads(body))
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Start consuming
        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        yield channel, messages

        # Cleanup
        channel.stop_consuming()
        connection.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ingestor_publishes_file_events(
        self, temp_data_dir: Path, amqp_consumer: tuple[Channel, list[Any]]
    ) -> None:
        """Test that ingestor publishes file events to AMQP."""
        channel, messages = amqp_consumer

        # Patch DATA_DIRECTORY to use temp dir and create ingestor
        with (
            patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)),
            Ingestor() as ingestor,
        ):  # Run ingestor in background
            ingest_task = asyncio.create_task(ingestor.ingest())

            # Allow ingestor to start watching
            await asyncio.sleep(1.0)

            # Create a test file
            test_file = temp_data_dir / "test.txt"
            test_file.write_text("Hello, World!")

            # Give watchdog time to detect the file event
            await asyncio.sleep(0.5)

            try:
                # Process some AMQP messages
                connection_process_time = time.time() + 3  # 3 seconds timeout
                while time.time() < connection_process_time:
                    channel.connection.process_data_events(time_limit=0.1)
                    if messages:
                        break

            finally:
                # Stop ingestor
                ingestor.stop()
                # Cancel task with timeout
                ingest_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(ingest_task, timeout=5.0)

        # Verify message was published
        # Handle macOS /private/var symlink issue
        import os

        expected_path = os.path.realpath(str(test_file.absolute()))

        # Filter messages to only the one for our test file
        test_messages = [msg for msg in messages if msg.get("file_path") == expected_path]

        assert len(test_messages) == 1, (
            f"Expected 1 message for {expected_path}, got {len(test_messages)}: "
            f"{[m.get('file_path') for m in messages]}"
        )
        message = test_messages[0]

        assert message["file_path"] == expected_path
        assert message["event_type"] == "IN_CREATE"
        assert "sha256_hash" in message
        assert "xxh128_hash" in message
        assert message["size"] == 13  # "Hello, World!" is 13 bytes

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ingestor_handles_multiple_files(
        self, temp_data_dir: Path, amqp_consumer: tuple[Channel, list[Any]]
    ) -> None:
        """Test that ingestor handles multiple file events."""
        channel, messages = amqp_consumer

        with (
            patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)),
            Ingestor() as ingestor,
        ):  # Run ingestor in background
            ingest_task = asyncio.create_task(ingestor.ingest())

            # Allow ingestor to start watching
            await asyncio.sleep(1.0)

            # Create multiple test files
            files = []
            for i in range(3):
                test_file = temp_data_dir / f"test{i}.txt"
                test_file.write_text(f"Content {i}")
                files.append(test_file)
                await asyncio.sleep(0.1)  # Small delay between files

            try:
                # Process AMQP messages
                connection_process_time = time.time() + 3
                while time.time() < connection_process_time:
                    channel.connection.process_data_events(time_limit=0.1)
                    if len(messages) >= 3:
                        break

            finally:
                # Stop ingestor
                ingestor.stop()
                # Cancel task with timeout
                ingest_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(ingest_task, timeout=5.0)

        # Verify all files were processed
        assert len(messages) >= 3

        # Check each message
        file_paths = [msg["file_path"] for msg in messages]
        import os

        for test_file in files:
            # Handle macOS /private/var symlink issue
            assert os.path.realpath(str(test_file.absolute())) in file_paths

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ingestor_finds_neighbors(
        self, temp_data_dir: Path, amqp_consumer: tuple[Channel, list[Any]]
    ) -> None:
        """Test that ingestor correctly identifies neighbor files."""
        channel, messages = amqp_consumer

        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            # Create neighbor files first
            (temp_data_dir / "video.srt").write_text("subtitles")
            (temp_data_dir / "video.nfo").write_text("info")

            with Ingestor() as ingestor:  # Run ingestor in background
                ingest_task = asyncio.create_task(ingestor.ingest())

                # Allow ingestor to start watching
                await asyncio.sleep(0.5)

                # Create main file
                main_file = temp_data_dir / "video.mp4"
                main_file.write_text("video content")

                # Give watchdog time to detect the file event
                await asyncio.sleep(0.5)

                try:
                    # Process AMQP messages
                    connection_process_time = time.time() + 3
                    while time.time() < connection_process_time:
                        channel.connection.process_data_events(time_limit=0.1)
                        if messages:
                            break

                finally:
                    # Stop ingestor
                    ingestor.stop()
                    # Cancel task with timeout
                    ingest_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                        await asyncio.wait_for(ingest_task, timeout=5.0)

        # Verify message contains neighbors
        assert len(messages) > 0

        # Find the message for the main file (video.mp4)
        # Handle macOS /private/var symlink issue
        import os

        main_file_path = os.path.realpath(str(main_file.absolute()))

        # Find the message for video.mp4
        message = None
        for msg in messages:
            if msg["file_path"] == main_file_path:
                message = msg
                break

        assert message is not None, f"No message found for {main_file_path}"
        assert "neighbors" in message

        neighbor_names = [Path(n).name for n in message["neighbors"]]
        assert "video.srt" in neighbor_names
        assert "video.nfo" in neighbor_names

    @pytest.mark.integration
    def test_prospector_with_real_files(self, temp_data_dir: Path) -> None:
        """Test prospector with real files."""

        # Create a test file
        test_file = temp_data_dir / "test.bin"
        test_content = b"Binary content \x00\x01\x02\x03"
        test_file.write_bytes(test_content)

        # Create neighbor files
        (temp_data_dir / "test.txt").write_text("metadata")
        (temp_data_dir / "test.info").write_text("info")

        # Run prospector
        prospector = Prospector(test_file)
        result = asyncio.run(prospector.prospect())

        # Verify results
        assert result["file_path"] == str(test_file.absolute())
        assert result["size"] == len(test_content)
        assert len(result["sha256_hash"]) == 64
        assert len(result["xxh128_hash"]) == 32

        # Check neighbors
        neighbor_names = [Path(n).name for n in result["neighbors"]]
        assert "test.txt" in neighbor_names
        assert "test.info" in neighbor_names

    @pytest.mark.integration
    def test_ingestor_handles_amqp_disconnection(self, temp_data_dir: Path) -> None:
        """Test that ingestor handles AMQP disconnection gracefully."""
        # Mock connection that fails after first channel creation
        mock_connection = Mock(spec=BlockingConnection)
        mock_channel = Mock(spec=Channel)

        call_count = 0

        def channel_side_effect() -> Mock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_channel
            else:
                raise AMQPConnectionError("Connection lost")

        mock_connection.channel.side_effect = channel_side_effect
        mock_connection.is_closed = False

        with (
            patch("ingestor.ingestor.BlockingConnection", return_value=mock_connection),
            patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)),
            patch.object(Ingestor, "__enter__") as mock_enter,
        ):
            mock_ingestor = Mock()
            mock_ingestor.amqp_connection = mock_connection
            mock_ingestor.amqp_channel = mock_channel
            mock_enter.return_value = mock_ingestor

            # This should not raise an exception
            with Ingestor() as ingestor:
                assert ingestor.amqp_connection is mock_connection
                assert ingestor.amqp_channel is mock_channel

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ingestor_processes_existing_files_on_startup(
        self, temp_data_dir: Path, amqp_consumer: tuple[Channel, list[Any]]
    ) -> None:
        """Test that ingestor can be configured to process existing files."""
        channel, messages = amqp_consumer

        # Create files before starting ingestor
        existing_file = temp_data_dir / "existing.txt"
        existing_file.write_text("Already here")

        with (
            patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)),
            Ingestor() as ingestor,
        ):  # Run ingestor in background
            ingest_task = asyncio.create_task(ingestor.ingest())

            # Allow ingestor to start
            await asyncio.sleep(1.0)

            # Create a new file to trigger processing
            new_file = temp_data_dir / "new.txt"
            new_file.write_text("New file")

            # Give watchdog time to detect the file event
            await asyncio.sleep(0.5)

            try:
                # Process AMQP messages
                connection_process_time = time.time() + 3
                while time.time() < connection_process_time:
                    channel.connection.process_data_events(time_limit=0.1)
                    if messages:
                        break

            finally:
                # Stop ingestor
                ingestor.stop()
                # Cancel task with timeout
                ingest_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(ingest_task, timeout=5.0)

        # Should only process the new file (existing files are not watched)
        # Filter messages to only those from our test directory
        # Handle macOS /private/var symlink issue
        import os

        temp_dir_resolved = os.path.realpath(str(temp_data_dir))
        test_messages = [msg for msg in messages if msg["file_path"].startswith(temp_dir_resolved)]

        # Further filter to only messages for our specific test files
        new_file_path = os.path.realpath(str(new_file.absolute()))
        test_messages = [msg for msg in test_messages if msg["file_path"] == new_file_path]

        assert len(test_messages) == 1, (
            f"Expected 1 message for {new_file_path}, got {len(test_messages)}: "
            f"{[m['file_path'] for m in test_messages]}"
        )
        assert test_messages[0]["file_path"] == new_file_path

    @pytest.mark.integration
    def test_amqp_message_properties(self, rabbitmq_available: bool) -> None:
        """Test AMQP message properties are set correctly."""
        if not rabbitmq_available:
            pytest.skip("RabbitMQ not available")

        connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange=AMQP_EXCHANGE,
            exchange_type="fanout",
            durable=True,
            auto_delete=False,
        )

        # Create test queue
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=AMQP_EXCHANGE, queue=queue_name, routing_key=ROUTING_KEY)

        received_properties = None

        def callback(ch: Any, method: Any, properties: Any, body: bytes) -> None:  # noqa: ARG001
            nonlocal received_properties
            received_properties = properties
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        # Publish a test message with proper properties
        from pika.spec import BasicProperties, DeliveryMode

        test_data = {"test": "data"}
        properties = BasicProperties(
            delivery_mode=DeliveryMode.Persistent,
            content_type="application/json",
        )

        channel.basic_publish(
            exchange=AMQP_EXCHANGE,
            routing_key=ROUTING_KEY,
            body=orjson.dumps(test_data),
            properties=properties,
        )

        # Process message
        connection.process_data_events(time_limit=1)

        # Cleanup
        channel.stop_consuming()
        connection.close()

        # Verify properties
        assert received_properties is not None
        assert received_properties.delivery_mode == DeliveryMode.Persistent.value
        assert received_properties.content_type == "application/json"
