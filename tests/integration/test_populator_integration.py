"""Integration tests for the populator service."""

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import orjson
import pytest
import pytest_asyncio
from aio_pika import Message, connect_robust
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import AMQPConnectionError
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from populator.populator import (
    AMQP_CONNECTION,
    AMQP_EXCHANGE,
    AMQP_QUEUE,
    AMQP_ROUTING_KEY,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    Populator,
)


class TestPopulatorIntegration:
    """Integration tests for populator service."""

    @pytest_asyncio.fixture
    async def rabbitmq_available(self) -> bool:
        """Check if RabbitMQ is available."""
        try:
            connection = await connect_robust(AMQP_CONNECTION)
            await connection.close()
            return True
        except (AMQPConnectionError, ConnectionError, OSError):
            return False

    @pytest_asyncio.fixture
    async def neo4j_available(self) -> bool:
        """Check if Neo4j is available."""
        try:
            driver = AsyncGraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
            )
            async with driver.session() as session:
                await session.run("RETURN 1")
            await driver.close()
            return True
        except (ServiceUnavailable, OSError):
            return False

    @pytest_asyncio.fixture
    async def amqp_publisher(
        self, rabbitmq_available: bool
    ) -> AsyncGenerator[tuple[Any, Any], None]:
        """Create an AMQP publisher for testing."""
        if not rabbitmq_available:
            pytest.skip("RabbitMQ not available")

        connection = await connect_robust(AMQP_CONNECTION)
        channel = await connection.channel()

        # Declare exchange
        exchange = await channel.declare_exchange(
            AMQP_EXCHANGE,
            type="fanout",
            durable=True,
            auto_delete=False,
        )

        # Purge the populator queue to ensure clean state
        try:
            queue = await channel.declare_queue(
                AMQP_QUEUE,
                durable=True,
                auto_delete=False,
            )
            await queue.purge()
            # Give more time for the purge to complete in CI
            await asyncio.sleep(0.5)
        except (AMQPConnectionError, AttributeError):
            # Queue might not exist yet or other transient errors
            pass

        yield channel, exchange

        await connection.close()

    @pytest_asyncio.fixture
    async def neo4j_driver(self, neo4j_available: bool) -> AsyncGenerator[Any, None]:
        """Create a Neo4j driver for testing."""
        if not neo4j_available:
            pytest.skip("Neo4j not available")

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        # Clean up test data before test
        async with driver.session() as session:
            await session.run("MATCH (n:File) WHERE n.path STARTS WITH '/test/' DETACH DELETE n")

        yield driver

        # Clean up test data after test
        async with driver.session() as session:
            await session.run("MATCH (n:File) WHERE n.path STARTS WITH '/test/' DETACH DELETE n")

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_processes_messages(
        self, amqp_publisher: tuple[Any, Any], neo4j_driver: Any
    ) -> None:
        """Test that populator processes messages and creates nodes in Neo4j."""
        channel, exchange = amqp_publisher

        # Prepare test message
        test_data = {
            "file_path": "/test/file1.txt",
            "sha256_hash": "abc123",
            "xxh128_hash": "def456",
            "size": 1024,
            "modified_time": "2024-01-01T00:00:00",
            "accessed_time": "2024-01-01T00:00:00",
            "changed_time": "2024-01-01T00:00:00",
            "timestamp": "2024-01-01T00:00:00",
            "event_type": "IN_CREATE",
            "neighbors": ["/test/file1.srt", "/test/file1.nfo"],
        }

        # Start populator
        async with Populator() as populator:
            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer time to set up
                await asyncio.sleep(1)

                # Publish message
                message = Message(
                    body=orjson.dumps(test_data),
                    delivery_mode=2,  # Persistent
                    content_type="application/json",
                )
                await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)

                # Give time to process
                await asyncio.sleep(2)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # Verify in Neo4j
        async with neo4j_driver.session() as session:
            # Check main file node
            result = await session.run(
                "MATCH (f:File {path: $path}) RETURN f", path="/test/file1.txt"
            )
            record = await result.single()
            assert record is not None

            file_node = record["f"]
            assert file_node["sha256"] == "abc123"
            assert file_node["xxh128"] == "def456"
            assert file_node["size"] == 1024

            # Check neighbor relationships
            result = await session.run(
                """
                MATCH (f1:File {path: $path})-[:NEIGHBOR]->(f2:File)
                RETURN f2.path as neighbor_path
                ORDER BY neighbor_path
                """,
                path="/test/file1.txt",
            )
            neighbors = [record["neighbor_path"] async for record in result]
            assert "/test/file1.nfo" in neighbors
            assert "/test/file1.srt" in neighbors

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_handles_multiple_messages(
        self, amqp_publisher: tuple[Any, Any], neo4j_driver: Any
    ) -> None:
        """Test that populator can handle multiple messages in sequence."""
        channel, exchange = amqp_publisher

        # Prepare multiple test messages
        messages_data = []
        for i in range(3):
            data = {
                "file_path": f"/test/file{i}.txt",
                "sha256_hash": f"hash{i}",
                "xxh128_hash": f"xxhash{i}",
                "size": 1024 * (i + 1),
                "modified_time": "2024-01-01T00:00:00",
                "accessed_time": "2024-01-01T00:00:00",
                "changed_time": "2024-01-01T00:00:00",
                "timestamp": "2024-01-01T00:00:00",
                "event_type": "IN_CREATE",
                "neighbors": [],
            }
            messages_data.append(data)

        # Start populator
        async with Populator() as populator:
            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer more time to set up and consume any stray messages in CI
                await asyncio.sleep(3)

                # Publish messages
                for data in messages_data:
                    message = Message(
                        body=orjson.dumps(data),
                        delivery_mode=2,
                        content_type="application/json",
                    )
                    await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)
                    await asyncio.sleep(0.2)  # More delay between messages for CI

                # Give more time to process in CI
                await asyncio.sleep(4)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # Verify all files in Neo4j
        async with neo4j_driver.session() as session:
            result = await session.run(
                "MATCH (f:File) WHERE f.path STARTS WITH '/test/' RETURN f ORDER BY f.path"
            )
            files = [record["f"] async for record in result]

            assert len(files) == 3
            for i, file_node in enumerate(files):
                assert file_node["path"] == f"/test/file{i}.txt"
                assert file_node["sha256"] == f"hash{i}"
                assert file_node["size"] == 1024 * (i + 1)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_updates_existing_nodes(
        self, amqp_publisher: tuple[Any, Any], neo4j_driver: Any
    ) -> None:
        """Test that populator updates existing nodes correctly."""
        channel, exchange = amqp_publisher

        # Create initial node
        async with neo4j_driver.session() as session:
            await session.run(
                """
                CREATE (f:File {
                    path: $path,
                    sha256: $sha256,
                    size: $size
                })
                """,
                path="/test/existing.txt",
                sha256="old_hash",
                size=500,
            )

        # Prepare update message
        update_data = {
            "file_path": "/test/existing.txt",
            "sha256_hash": "new_hash",
            "xxh128_hash": "new_xxhash",
            "size": 1000,
            "modified_time": "2024-01-02T00:00:00",
            "accessed_time": "2024-01-02T00:00:00",
            "changed_time": "2024-01-02T00:00:00",
            "timestamp": "2024-01-02T00:00:00",
            "event_type": "IN_MODIFY",
            "neighbors": [],
        }

        # Start populator
        async with Populator() as populator:
            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer time to set up
                await asyncio.sleep(1)

                # Publish update message
                message = Message(
                    body=orjson.dumps(update_data),
                    delivery_mode=2,
                    content_type="application/json",
                )
                await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)

                # Give time to process
                await asyncio.sleep(2)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # Verify node was updated
        async with neo4j_driver.session() as session:
            result = await session.run(
                "MATCH (f:File {path: $path}) RETURN f", path="/test/existing.txt"
            )
            record = await result.single()
            assert record is not None

            file_node = record["f"]
            assert file_node["sha256"] == "new_hash"
            assert file_node["xxh128"] == "new_xxhash"
            assert file_node["size"] == 1000
            assert file_node["event_type"] == "IN_MODIFY"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_handles_message_errors(self, amqp_publisher: tuple[Any, Any]) -> None:
        """Test that populator handles malformed messages gracefully."""
        channel, exchange = amqp_publisher

        # Prepare malformed messages
        messages = [
            b"not json",  # Invalid JSON
            orjson.dumps({}),  # Missing required fields
            orjson.dumps({"file_path": None}),  # Invalid field value
        ]

        # Track processed messages
        processed = []

        # Mock process_message to track calls
        async def mock_process(message: AbstractIncomingMessage) -> None:
            processed.append(message)
            await original_process(message)

        # Start populator
        async with Populator() as populator:
            original_process = populator.process_message
            # Use setattr to avoid mypy method assignment error
            setattr(populator, "process_message", mock_process)  # noqa: B010

            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer time to set up
                await asyncio.sleep(1)

                # Publish malformed messages
                for msg_body in messages:
                    message = Message(
                        body=msg_body,
                        delivery_mode=2,
                    )
                    await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)

                # Give time to process
                await asyncio.sleep(2)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # All messages should have been processed (not crashed)
        assert len(processed) == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_reconnects_to_services(self) -> None:
        """Test that populator can reconnect to services after disconnection."""
        # Mock connections that fail initially then succeed
        amqp_connect_attempts = 0
        neo4j_connect_attempts = 0

        async def mock_amqp_connect(*args: Any, **kwargs: Any) -> AsyncMock:  # noqa: ARG001
            nonlocal amqp_connect_attempts
            amqp_connect_attempts += 1
            if amqp_connect_attempts == 1:
                raise AMQPConnectionError("Connection failed")
            # Create a proper mock for AMQP connection
            mock_conn = AsyncMock()
            mock_channel = AsyncMock()
            mock_conn.channel.return_value = mock_channel
            return mock_conn

        def mock_neo4j_driver(*args: Any, **kwargs: Any) -> AsyncMock:  # noqa: ARG001
            nonlocal neo4j_connect_attempts
            neo4j_connect_attempts += 1
            if neo4j_connect_attempts == 1:
                raise ServiceUnavailable("Connection failed")

            driver = AsyncMock()
            session = AsyncMock()
            # Create a proper async context manager for session
            session_context = AsyncMock()
            session_context.__aenter__ = AsyncMock(return_value=session)
            session_context.__aexit__ = AsyncMock(return_value=None)
            driver.session = Mock(return_value=session_context)
            session.run = AsyncMock()  # Mock the run method for connection verification
            return driver

        with (
            patch("populator.populator.connect_robust", side_effect=mock_amqp_connect),
            patch("populator.populator.AsyncGraphDatabase.driver", side_effect=mock_neo4j_driver),
        ):
            # First attempt should fail with AMQP error
            with pytest.raises(AMQPConnectionError):
                async with Populator() as populator:
                    pass

            # Reset Neo4j attempts since it wasn't reached in first attempt
            neo4j_connect_attempts = 0

            # Second attempt - AMQP succeeds but Neo4j fails
            with pytest.raises(ServiceUnavailable):
                async with Populator() as populator:
                    pass

            # Third attempt should succeed (both services connect)
            async with Populator() as populator:
                assert populator.amqp_connection is not None
                assert populator.neo4j_driver is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_creates_complex_graph(
        self, amqp_publisher: tuple[Any, Any], neo4j_driver: Any
    ) -> None:
        """Test that populator correctly creates complex file relationships."""
        channel, exchange = amqp_publisher

        # Create a complex set of files with relationships
        files = [
            {
                "file_path": "/test/project/main.py",
                "neighbors": ["/test/project/main_test.py", "/test/project/README.md"],
            },
            {
                "file_path": "/test/project/main_test.py",
                "neighbors": ["/test/project/main.py", "/test/project/conftest.py"],
            },
            {
                "file_path": "/test/project/README.md",
                "neighbors": ["/test/project/main.py", "/test/project/LICENSE"],
            },
        ]

        # Start populator
        async with Populator() as populator:
            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer time to set up
                await asyncio.sleep(1)

                # Publish messages
                for file_info in files:
                    data = {
                        "file_path": file_info["file_path"],
                        "sha256_hash": "hash",
                        "xxh128_hash": "xxhash",
                        "size": 1000,
                        "modified_time": "2024-01-01T00:00:00",
                        "accessed_time": "2024-01-01T00:00:00",
                        "changed_time": "2024-01-01T00:00:00",
                        "timestamp": "2024-01-01T00:00:00",
                        "event_type": "IN_CREATE",
                        "neighbors": file_info["neighbors"],
                    }

                    message = Message(
                        body=orjson.dumps(data),
                        delivery_mode=2,
                        content_type="application/json",
                    )
                    await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)

                # Give time to process
                await asyncio.sleep(3)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # Verify graph structure
        async with neo4j_driver.session() as session:
            # Count total nodes
            result = await session.run(
                "MATCH (f:File) WHERE f.path STARTS WITH '/test/project/' RETURN count(f) as count"
            )
            record = await result.single()
            # Should have created nodes for all files and their neighbors
            assert record["count"] >= 5

            # Check specific relationships
            result = await session.run(
                """
                MATCH (f1:File {path: $path})-[:NEIGHBOR]->(f2:File)
                RETURN f2.path as neighbor
                ORDER BY neighbor
                """,
                path="/test/project/main.py",
            )
            neighbors = [record["neighbor"] async for record in result]
            assert "/test/project/README.md" in neighbors
            assert "/test/project/main_test.py" in neighbors

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_populator_handles_concurrent_messages(
        self, amqp_publisher: tuple[Any, Any], neo4j_driver: Any
    ) -> None:
        """Test that populator correctly handles concurrent message processing."""
        channel, exchange = amqp_publisher

        # Prepare many messages
        num_messages = 10
        messages_data = []
        for i in range(num_messages):
            data = {
                "file_path": f"/test/concurrent/file{i}.txt",
                "sha256_hash": f"hash{i}",
                "xxh128_hash": f"xxhash{i}",
                "size": 1000,
                "modified_time": "2024-01-01T00:00:00",
                "accessed_time": "2024-01-01T00:00:00",
                "changed_time": "2024-01-01T00:00:00",
                "timestamp": "2024-01-01T00:00:00",
                "event_type": "IN_CREATE",
                "neighbors": [],
            }
            messages_data.append(data)

        # Start populator
        async with Populator() as populator:
            # Run consumer in background
            consume_task = asyncio.create_task(populator.consume())

            try:
                # Give consumer time to set up
                await asyncio.sleep(1)

                # Publish all messages rapidly
                for data in messages_data:
                    message = Message(
                        body=orjson.dumps(data),
                        delivery_mode=2,
                        content_type="application/json",
                    )
                    await exchange.publish(message, routing_key=AMQP_ROUTING_KEY)

                # Give time to process all messages
                await asyncio.sleep(5)

            finally:
                # Stop populator
                populator.stop()
                # Cancel task with timeout
                consume_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                    await asyncio.wait_for(consume_task, timeout=5.0)

        # Verify all files were created
        async with neo4j_driver.session() as session:
            result = await session.run(
                "MATCH (f:File) WHERE f.path STARTS WITH '/test/concurrent/' "
                "RETURN count(f) as count"
            )
            record = await result.single()
            assert record["count"] == num_messages
