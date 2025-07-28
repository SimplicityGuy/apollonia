"""Integration tests for AMQP functionality."""

from __future__ import annotations

import asyncio
import contextlib
import os
import time
from typing import Any

import orjson
import pika
import pytest
from aio_pika import Message, connect_robust
from pika import BlockingConnection, URLParameters

pytestmark = pytest.mark.integration


@pytest.fixture
def amqp_url() -> str:
    """Get AMQP connection URL from environment or use default."""
    return os.getenv("AMQP_CONNECTION_STRING", "amqp://guest:guest@localhost:5672/")


@pytest.fixture
def skip_if_no_amqp(amqp_url: str) -> None:
    """Skip test if AMQP is not available."""
    try:
        conn = BlockingConnection(URLParameters(amqp_url))
        conn.close()
    except Exception:
        pytest.skip("AMQP server not available")


class TestAMQPIntegration:
    """Test AMQP integration between services."""

    def test_blocking_connection(self, amqp_url: str, skip_if_no_amqp: None) -> None:  # noqa: ARG002
        """Test basic blocking connection (used by ingestor)."""
        connection = BlockingConnection(URLParameters(amqp_url))
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange="apollonia-test", exchange_type="fanout", durable=True, auto_delete=True
        )

        # Declare queue
        channel.queue_declare(queue="apollonia-test-queue", durable=True, auto_delete=True)

        # Bind queue to exchange
        channel.queue_bind(exchange="apollonia-test", queue="apollonia-test-queue")

        # Publish a test message
        test_data = {"test": "message", "timestamp": time.time()}
        channel.basic_publish(
            exchange="apollonia-test",
            routing_key="",
            body=orjson.dumps(test_data),
            properties=pika.spec.BasicProperties(
                content_encoding="application/json", delivery_mode=2
            ),
        )

        # Consume the message
        method, properties, body = channel.basic_get("apollonia-test-queue")
        assert method is not None
        assert properties.content_encoding == "application/json"

        received_data = orjson.loads(body)
        assert received_data == test_data

        # Acknowledge
        channel.basic_ack(method.delivery_tag)

        # Cleanup
        channel.queue_delete("apollonia-test-queue")
        channel.exchange_delete("apollonia-test")
        connection.close()

    @pytest.mark.asyncio
    async def test_async_connection(self, amqp_url: str, skip_if_no_amqp: None) -> None:  # noqa: ARG002
        """Test async connection (used by populator)."""
        connection = await connect_robust(amqp_url)

        async with connection:
            channel = await connection.channel()

            # Declare exchange
            exchange = await channel.declare_exchange(
                "apollonia-test-async", type="fanout", durable=True, auto_delete=True
            )

            # Declare queue
            queue = await channel.declare_queue(
                "apollonia-test-async-queue", durable=True, auto_delete=True
            )

            # Bind queue
            await queue.bind(exchange)

            # Publish test message
            test_data = {"async": "test", "value": 42}
            await exchange.publish(
                Message(
                    body=orjson.dumps(test_data),
                    content_encoding="application/json",
                    delivery_mode=2,
                ),
                routing_key="",
            )

            # Consume message
            incoming_message = await queue.get(timeout=5.0)
            assert incoming_message is not None

            async with incoming_message.process():
                received_data = orjson.loads(incoming_message.body)
                assert received_data == test_data

            # Cleanup
            await queue.delete()
            await exchange.delete()

    @pytest.mark.asyncio
    async def test_message_flow(self, amqp_url: str, skip_if_no_amqp: None) -> None:  # noqa: ARG002
        """Test complete message flow from publisher to consumer."""
        # Setup connection
        connection = await connect_robust(amqp_url)

        async with connection:
            channel = await connection.channel()

            # Use the actual apollonia exchange/queue names
            exchange = await channel.declare_exchange(
                "apollonia", type="fanout", durable=True, auto_delete=False
            )

            queue = await channel.declare_queue(
                "apollonia-integration-test", durable=True, auto_delete=True
            )

            await queue.bind(exchange, routing_key="file.created")

            # Simulate ingestor publishing
            file_metadata = {
                "file_path": "/data/test-integration.txt",
                "event_type": "IN_CREATE",
                "sha256_hash": "abc123",
                "xxh128_hash": "def456",
                "size": 1024,
                "timestamp": "2024-01-01T12:00:00+00:00",
                "neighbors": [],
            }

            await exchange.publish(
                Message(
                    body=orjson.dumps(file_metadata),
                    content_encoding="application/json",
                    delivery_mode=2,
                ),
                routing_key="file.created",
            )

            # Simulate populator consuming
            messages_received = []

            async def process_message(message: Any) -> None:
                async with message.process():
                    data = orjson.loads(message.body)
                    messages_received.append(data)

            # Consume one message
            await queue.consume(process_message, no_ack=False)

            # Wait for message
            await asyncio.sleep(0.5)

            # Verify
            assert len(messages_received) == 1
            assert messages_received[0] == file_metadata

            # Cleanup
            await queue.delete()

    def test_error_handling(self, amqp_url: str, skip_if_no_amqp: None) -> None:  # noqa: ARG002
        """Test error handling and recovery."""
        connection = BlockingConnection(URLParameters(amqp_url))
        channel = connection.channel()

        # Try to consume from non-existent queue
        with pytest.raises((ValueError, RuntimeError)):
            channel.basic_get("non-existent-queue")

        # Connection should still be usable
        assert connection.is_open

        connection.close()

    @pytest.mark.asyncio
    async def test_concurrent_consumers(self, amqp_url: str, skip_if_no_amqp: None) -> None:  # noqa: ARG002
        """Test multiple consumers on same queue."""
        connection = await connect_robust(amqp_url)

        async with connection:
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                "apollonia-concurrent-test", type="fanout", durable=True, auto_delete=True
            )

            queue = await channel.declare_queue(
                "apollonia-concurrent-queue", durable=True, auto_delete=True
            )

            await queue.bind(exchange)

            # Publish multiple messages
            num_messages = 10
            for i in range(num_messages):
                await exchange.publish(
                    Message(body=orjson.dumps({"id": i}), content_encoding="application/json"),
                    routing_key="",
                )

            # Simulate multiple consumers
            consumed_messages = []

            async def consumer(consumer_id: int) -> None:
                async with connection.channel() as consumer_channel:
                    consumer_queue = await consumer_channel.get_queue("apollonia-concurrent-queue")

                    async for message in consumer_queue:  # type: ignore[attr-defined]
                        async with message.process():
                            data = orjson.loads(message.body)
                            consumed_messages.append((consumer_id, data["id"]))

                            if len(consumed_messages) >= num_messages:
                                break

            # Start consumers
            consumer_tasks = [asyncio.create_task(consumer(i)) for i in range(3)]

            # Wait for all messages to be consumed
            await asyncio.sleep(1.0)

            # Cancel consumers
            for task in consumer_tasks:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            # Verify all messages were consumed
            message_ids = [msg[1] for msg in consumed_messages]
            assert len(set(message_ids)) == num_messages

            # Cleanup
            await queue.delete()
            await exchange.delete()
