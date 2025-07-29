"""End-to-end integration tests for the complete Apollonia pipeline."""
# mypy: disable-error-code="name-defined"
# ruff: noqa: SIM117

import asyncio
import contextlib
import logging
import os
import tempfile
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import patch

import orjson
import pytest
import pytest_asyncio
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable
from pika import BasicProperties, BlockingConnection, URLParameters
from pika.exceptions import AMQPConnectionError

from ingestor.ingestor import AMQP_CONNECTION as INGESTOR_AMQP
from ingestor.ingestor import AMQP_EXCHANGE, Ingestor
from populator.populator import (
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    Populator,
)

logger = logging.getLogger(__name__)


class TestEndToEnd:
    """End-to-end tests for the complete pipeline."""

    @pytest.fixture
    def services_available(self) -> bool:
        """Check if all required services are available."""
        # Check RabbitMQ
        try:
            connection = BlockingConnection(URLParameters(INGESTOR_AMQP))
            connection.close()
            rabbitmq_ok = True
        except (AMQPConnectionError, ConnectionError):
            rabbitmq_ok = False

        # Check Neo4j
        try:
            driver = AsyncGraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
            )

            async def check_neo4j() -> None:
                async with driver.session() as session:
                    await session.run("RETURN 1")
                await driver.close()

            asyncio.run(check_neo4j())
            neo4j_ok = True
        except (ServiceUnavailable, OSError):
            neo4j_ok = False

        if not rabbitmq_ok or not neo4j_ok:
            pytest.skip(
                f"Required services not available (RabbitMQ: {rabbitmq_ok}, Neo4j: {neo4j_ok})"
            )

        return True

    @pytest.fixture
    def temp_data_dir(self) -> Generator[Path, None, None]:
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest_asyncio.fixture
    async def clean_neo4j(self, services_available: bool) -> AsyncGenerator[None, None]:  # noqa: ARG002
        """Clean up Neo4j before and after tests."""
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        # Clean ALL File nodes before test to ensure test isolation
        async with driver.session() as session:
            result = await session.run("MATCH (n:File) RETURN count(n) as count")
            record = await result.single()
            count = record["count"] if record else 0
            logger.info("[CLEANUP] Before test: %d File nodes in Neo4j", count)

            await session.run("MATCH (n:File) DETACH DELETE n")
            logger.info("[CLEANUP] Deleted all File nodes before test")

        yield

        # Clean ALL File nodes after test
        async with driver.session() as session:
            result = await session.run("MATCH (n:File) RETURN count(n) as count")
            record = await result.single()
            count = record["count"] if record else 0
            logger.info("[CLEANUP] After test: %d File nodes in Neo4j", count)

            await session.run("MATCH (n:File) DETACH DELETE n")
            logger.info("[CLEANUP] Deleted all File nodes after test")

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_file_ingestion_to_neo4j(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test complete pipeline from file creation to Neo4j storage."""
        # Patch DATA_DIRECTORY for ingestor
        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            # Start both services
            with Ingestor() as ingestor:
                # Use a unique queue name for this test
                test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                async with Populator(queue_name=test_queue_name) as populator:
                    # Run services in background
                    ingest_task = asyncio.create_task(ingestor.ingest())
                    consume_task = asyncio.create_task(populator.consume())

                    try:
                        # Give services time to start
                        await asyncio.sleep(2)

                        # Create test files
                        test_files = []
                        for i in range(3):
                            file_path = temp_data_dir / f"test_file_{i}.txt"
                            file_path.write_text(f"This is test file {i}")
                            test_files.append(file_path)
                            await asyncio.sleep(0.5)  # Small delay between files

                        # Give time for processing
                        await asyncio.sleep(5)

                    finally:
                        # Stop services
                        ingestor.stop()
                        populator.stop()

                        # Cancel tasks with timeout
                        for task in [ingest_task, consume_task]:
                            task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(task, timeout=5.0)

        # Verify in Neo4j
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Count created nodes - be specific to avoid nodes from other tests
            import os

            temp_dir_path = os.path.realpath(str(temp_data_dir))

            # Debug: Check what files exist in Neo4j
            debug_result = await session.run("MATCH (f:File) RETURN f.path as path ORDER BY path")
            all_paths = [record["path"] async for record in debug_result]
            logger.info("[DEBUG] All files in Neo4j: %s", all_paths)

            result = await session.run(
                """
                MATCH (f:File) WHERE f.path STARTS WITH $dir
                AND f.path CONTAINS 'test_file_'
                RETURN count(f) as count
                """,
                dir=temp_dir_path,
            )
            record = await result.single()
            count = record["count"] if record else None
            logger.info("[DEBUG] Count for dir %s: %s", temp_dir_path, count)
            assert record is not None and record["count"] == 3

            # Verify file properties
            for i, test_file in enumerate(test_files):
                # Handle macOS /private/var symlink issue
                import os

                real_path = os.path.realpath(str(test_file.absolute()))
                result = await session.run("MATCH (f:File {path: $path}) RETURN f", path=real_path)
                record = await result.single()
                assert record is not None

                file_node = record["f"]
                assert file_node["size"] == len(f"This is test file {i}")
                assert len(file_node["sha256"]) == 64
                assert len(file_node["xxh128"]) == 32
                assert file_node["event_type"] == "IN_CREATE"

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_neighbor_file_relationships(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test that neighbor file relationships are correctly created."""
        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            with Ingestor() as ingestor:
                # Use a unique queue name for this test
                test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                async with Populator(queue_name=test_queue_name) as populator:
                    # Run services
                    ingest_task = asyncio.create_task(ingestor.ingest())
                    consume_task = asyncio.create_task(populator.consume())

                    try:
                        # Give services more time to start in CI
                        await asyncio.sleep(4)

                        # Create files AFTER watchdog is running
                        # Create neighbor files first
                        (temp_data_dir / "movie.srt").write_text("subtitles")
                        (temp_data_dir / "movie.nfo").write_text("metadata")
                        (temp_data_dir / "movie.jpg").write_text("thumbnail")

                        # More delay to ensure neighbor files are on disk in CI
                        await asyncio.sleep(1)

                        # Create the main file to trigger processing
                        main_file = temp_data_dir / "movie.mp4"
                        main_file.write_text("video content")

                        # Give more time for processing in CI
                        await asyncio.sleep(7)

                    finally:
                        # Stop services
                        ingestor.stop()
                        populator.stop()

                        # Cancel tasks with timeout
                        for task in [ingest_task, consume_task]:
                            task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(task, timeout=5.0)

        # Verify relationships in Neo4j
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Check main file and its neighbors
            result = await session.run(
                """
                MATCH (f:File)-[:NEIGHBOR]->(n:File)
                WHERE f.path CONTAINS 'movie.mp4'
                RETURN n.path as neighbor_path
                ORDER BY neighbor_path
                """
            )
            neighbors = [record["neighbor_path"] async for record in result]

            # Should have created neighbor relationships
            assert any("movie.srt" in path for path in neighbors)
            assert any("movie.nfo" in path for path in neighbors)
            assert any("movie.jpg" in path for path in neighbors)

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_file_update_handling(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test that file updates are correctly handled."""
        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            with Ingestor() as ingestor:
                # Use a unique queue name for this test
                test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                async with Populator(queue_name=test_queue_name) as populator:
                    # Run services
                    ingest_task = asyncio.create_task(ingestor.ingest())
                    consume_task = asyncio.create_task(populator.consume())

                    try:
                        # Give services more time to start in CI
                        await asyncio.sleep(4)

                        # Create initial file AFTER watchdog is running
                        test_file = temp_data_dir / "update_test.txt"
                        test_file.write_text("Initial content")

                        # Give more time to process initial file in CI
                        await asyncio.sleep(5)

                        # Update the file
                        test_file.write_text("Updated content with more text")

                        # Give more time for processing the update in CI
                        await asyncio.sleep(5)

                    finally:
                        # Stop services
                        ingestor.stop()
                        populator.stop()

                        # Cancel tasks with timeout
                        for task in [ingest_task, consume_task]:
                            task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(task, timeout=5.0)

        # Verify in Neo4j
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Handle macOS /private/var symlink issue
            import os

            result = await session.run(
                "MATCH (f:File {path: $path}) RETURN f",
                path=os.path.realpath(str(test_file.absolute())),
            )
            record = await result.single()
            assert record is not None

            file_node = record["f"]
            # Size should reflect the updated content
            assert file_node["size"] == len("Updated content with more text")
            # Hash should be different from initial content
            assert len(file_node["sha256"]) == 64

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test that multiple files can be processed concurrently."""
        num_files = 10

        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            with Ingestor() as ingestor:
                # Use a unique queue name for this test
                test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                async with Populator(queue_name=test_queue_name) as populator:
                    # Run services
                    ingest_task = asyncio.create_task(ingestor.ingest())
                    consume_task = asyncio.create_task(populator.consume())

                    try:
                        # Give services time to start
                        await asyncio.sleep(2)

                        # Create multiple files rapidly
                        import os

                        test_files = []
                        for i in range(num_files):
                            file_path = temp_data_dir / f"concurrent_{i}.dat"
                            file_path.write_bytes(os.urandom(1024))  # Random 1KB content
                            test_files.append(file_path)

                        # Give time for processing
                        await asyncio.sleep(10)

                    finally:
                        # Stop services
                        ingestor.stop()
                        populator.stop()

                        # Cancel tasks with timeout
                        for task in [ingest_task, consume_task]:
                            task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(task, timeout=5.0)

        # Verify all files were processed
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Be specific about the path to avoid counting files from other tests
            import os

            temp_dir_path = os.path.realpath(str(temp_data_dir))
            result = await session.run(
                """
                MATCH (f:File) WHERE f.path STARTS WITH $dir
                AND f.path CONTAINS 'concurrent_'
                RETURN count(f) as count
                """,
                dir=temp_dir_path,
            )
            record = await result.single()
            assert record is not None and record["count"] == num_files

            # Verify each file has correct size
            for test_file in test_files:
                # Handle macOS /private/var symlink issue
                import os

                test_path = os.path.realpath(str(test_file.absolute()))
                logger.info("[DEBUG] Checking file: %s", test_path)

                # First check if file exists and what properties it has
                debug_result = await session.run(
                    "MATCH (f:File {path: $path}) RETURN f",
                    path=test_path,
                )
                debug_record = await debug_result.single()
                if debug_record:
                    logger.info("[DEBUG] File properties: %s", dict(debug_record["f"]))
                else:
                    logger.error("[DEBUG] File not found: %s", test_path)

                result = await session.run(
                    "MATCH (f:File {path: $path}) RETURN f.size as size",
                    path=test_path,
                )
                record = await result.single()
                assert record is not None and record["size"] == 1024

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_resilience(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test that services can recover from temporary failures."""
        test_file = temp_data_dir / "resilience_test.txt"

        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            # Start ingestor first
            with Ingestor() as ingestor:
                ingest_task = asyncio.create_task(ingestor.ingest())

                # Create file while populator is not running
                test_file.write_text("Content created before populator")

                try:
                    # Wait a bit
                    await asyncio.sleep(2)

                    # Now start populator - it should process queued messages
                    test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                    async with Populator(queue_name=test_queue_name) as populator:
                        consume_task = asyncio.create_task(populator.consume())

                        try:
                            # Give time to process queued message
                            await asyncio.sleep(3)

                            # Create another file while both are running
                            test_file2 = temp_data_dir / "resilience_test2.txt"
                            test_file2.write_text("Content created with both running")

                            # Give time to process
                            await asyncio.sleep(3)

                        finally:
                            # Stop populator
                            populator.stop()
                            # Cancel consume_task with timeout
                            consume_task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(consume_task, timeout=5.0)

                finally:
                    # Stop ingestor
                    ingestor.stop()
                    # Cancel ingest_task with timeout
                    ingest_task.cancel()
                    with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                        await asyncio.wait_for(ingest_task, timeout=5.0)

        # Verify both files were processed
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Be specific about the path to avoid finding files from other tests
            import os

            temp_dir_path = os.path.realpath(str(temp_data_dir))

            # Debug: Check what's in Neo4j
            debug_result = await session.run(
                """
                MATCH (f:File) WHERE f.path CONTAINS 'resilience_test'
                RETURN f.path as path, f.event_type as event_type
                ORDER BY path
                """
            )
            debug_records = [(r["path"], r["event_type"]) async for r in debug_result]
            logger.info("[DEBUG] Resilience test files in Neo4j: %s", debug_records)

            result = await session.run(
                """
                MATCH (f:File) WHERE f.path STARTS WITH $dir
                AND f.path CONTAINS 'resilience_test'
                RETURN DISTINCT f.path as path ORDER BY path
                """,
                dir=temp_dir_path,
            )
            paths = [record["path"] async for record in result]
            logger.info("[DEBUG] Distinct paths found: %s", paths)

            assert len(paths) == 2
            assert any("resilience_test.txt" in path for path in paths)
            assert any("resilience_test2.txt" in path for path in paths)

        await driver.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_persistence(self, services_available: bool) -> None:  # noqa: ARG002
        """Test that messages are persisted in RabbitMQ."""
        # This test verifies RabbitMQ configuration
        connection = BlockingConnection(URLParameters(INGESTOR_AMQP))
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange=AMQP_EXCHANGE,
            exchange_type="fanout",
            durable=True,
            auto_delete=False,
        )

        # Create and bind a test queue (use unique name to avoid conflicts)
        test_queue = f"test_persistence_{os.getpid()}"
        result = channel.queue_declare(queue=test_queue, durable=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=AMQP_EXCHANGE, queue=queue_name, routing_key="")

        # Publish a test message
        test_data = {"test": "persistence"}
        channel.basic_publish(
            exchange=AMQP_EXCHANGE,
            routing_key="",
            body=orjson.dumps(test_data),
            properties=BasicProperties(delivery_mode=2),
        )

        # Close connection
        connection.close()

        # Reconnect and check message is still there
        connection2 = BlockingConnection(URLParameters(INGESTOR_AMQP))
        channel2 = connection2.channel()

        # Get message
        method, properties, body = channel2.basic_get(queue_name)

        assert method is not None
        assert properties.delivery_mode == 2  # Persistent
        assert orjson.loads(body) == test_data

        # Cleanup
        channel2.queue_delete(queue_name)
        connection2.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_file_handling(
        self,
        services_available: bool,  # noqa: ARG002
        temp_data_dir: Path,
        clean_neo4j: None,  # noqa: ARG002
    ) -> None:
        """Test handling of large files."""
        with patch("ingestor.ingestor.DATA_DIRECTORY", str(temp_data_dir)):
            with Ingestor() as ingestor:
                # Use a unique queue name for this test
                test_queue_name = f"apollonia-test-{uuid.uuid4().hex[:8]}"
                async with Populator(queue_name=test_queue_name) as populator:
                    # Run services
                    ingest_task = asyncio.create_task(ingestor.ingest())
                    consume_task = asyncio.create_task(populator.consume())

                    try:
                        # Give services time to start
                        await asyncio.sleep(2)

                        # Create large file AFTER watchdog is running
                        import os

                        large_file = temp_data_dir / "large_file.bin"
                        large_content = os.urandom(10 * 1024 * 1024)  # 10MB
                        large_file.write_bytes(large_content)

                        # Give more time for processing large file
                        await asyncio.sleep(10)

                    finally:
                        # Stop services
                        ingestor.stop()
                        populator.stop()

                        # Cancel tasks with timeout
                        for task in [ingest_task, consume_task]:
                            task.cancel()
                            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                                await asyncio.wait_for(task, timeout=5.0)

        # Verify in Neo4j
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        async with driver.session() as session:
            # Handle macOS /private/var symlink issue
            import os

            large_file_path = os.path.realpath(str(large_file.absolute()))
            logger.info("[DEBUG] Looking for large file at: %s", large_file_path)

            # Debug: Check all files in Neo4j
            debug_result = await session.run(
                "MATCH (f:File) RETURN f.path as path, f.size as size ORDER BY path"
            )
            all_files = [(r["path"], r["size"]) async for r in debug_result]
            logger.info("[DEBUG] All files in Neo4j: %s", all_files)

            result = await session.run(
                "MATCH (f:File {path: $path}) RETURN f",
                path=large_file_path,
            )
            record = await result.single()
            assert record is not None

            file_node = record["f"]
            assert file_node["size"] == 10 * 1024 * 1024
            assert len(file_node["sha256"]) == 64
            assert len(file_node["xxh128"]) == 32

        await driver.close()
