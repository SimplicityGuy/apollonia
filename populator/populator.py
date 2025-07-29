"""Neo4j populator service for Apollonia."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from typing import TYPE_CHECKING, Any

import orjson
from aio_pika import connect_robust
from neo4j import AsyncGraphDatabase

if TYPE_CHECKING:
    from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
    from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

# Configuration
AMQP_CONNECTION = os.getenv("AMQP_CONNECTION_STRING", "amqp://apollonia:apollonia@localhost:5672/")
AMQP_EXCHANGE = "apollonia"
AMQP_QUEUE = "apollonia-populator"
AMQP_ROUTING_KEY = "file.created"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class Populator:
    """Service that consumes file metadata from AMQP and imports to Neo4j."""

    def __init__(self) -> None:
        """Initialize the populator."""
        self.amqp_connection: AbstractRobustConnection | None = None
        self.neo4j_driver: AsyncDriver | None = None
        self._running = True

    async def __aenter__(self) -> Populator:
        """Set up connections."""
        logger.info("🔌 Connecting to AMQP broker at %s", AMQP_CONNECTION)
        self.amqp_connection = await connect_robust(AMQP_CONNECTION)

        logger.info("🔌 Connecting to Neo4j at %s", NEO4J_URI)
        self.neo4j_driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        # Verify Neo4j connection
        async with self.neo4j_driver.session() as session:
            await session.run("RETURN 1")
        logger.info("✅ Neo4j connection verified")

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Clean up connections."""
        if self.amqp_connection:
            await self.amqp_connection.close()
            logger.info("🔌 AMQP connection closed")

        if self.neo4j_driver:
            await self.neo4j_driver.close()
            logger.info("🔌 Neo4j connection closed")

    def stop(self) -> None:
        """Signal the populator to stop."""
        logger.info("🛑 Stopping populator")
        self._running = False

    async def process_message(self, message: AbstractIncomingMessage) -> None:
        """Process a single message from the queue.

        Args:
            message: The incoming AMQP message containing file metadata.
        """
        async with message.process():
            try:
                # Parse message body
                try:
                    data = orjson.loads(message.body)
                except orjson.JSONDecodeError:
                    logger.warning("⚠️ Skipping invalid JSON message")
                    return

                # Validate required fields
                file_path = data.get("file_path")
                if not file_path:
                    logger.warning("⚠️ Skipping message with missing file_path")
                    return

                logger.info("🔍 Processing file: %s", file_path)

                # Import to Neo4j
                await self._import_to_neo4j(data)

            except Exception:
                logger.exception("💥 Error processing message")
                # Message will be requeued due to exception in process context

    async def _import_to_neo4j(self, data: dict[str, Any]) -> None:
        """Import file metadata to Neo4j.

        Args:
            data: File metadata dictionary.
        """
        if not self.neo4j_driver:
            return

        async with self.neo4j_driver.session() as session:
            # Create or update File node
            query = """
            MERGE (f:File {path: $file_path})
            SET f.sha256 = $sha256_hash,
                f.xxh128 = $xxh128_hash,
                f.size = $size,
                f.modified = datetime($modified_time),
                f.accessed = datetime($accessed_time),
                f.changed = datetime($changed_time),
                f.discovered = datetime($timestamp),
                f.event_type = $event_type
            RETURN f
            """

            # Validate required fields
            if "file_path" not in data:
                logger.error("Missing required field 'file_path' in message data: %s", data)
                return

            params = {
                "file_path": data["file_path"],
                "sha256_hash": data.get("sha256_hash", ""),
                "xxh128_hash": data.get("xxh128_hash", ""),
                "size": data.get("size", 0),
                "modified_time": data.get("modified_time"),
                "accessed_time": data.get("accessed_time"),
                "changed_time": data.get("changed_time"),
                "timestamp": data.get("timestamp"),
                "event_type": data.get("event_type", "IN_CREATE"),
            }

            result = await session.run(query, params)
            file_record = await result.single()

            if file_record:
                logger.debug("✅ Created/updated file node: %s", data["file_path"])

            # Create relationships to neighbor files
            for neighbor_path in data.get("neighbors", []):
                neighbor_query = """
                MERGE (f1:File {path: $file_path})
                MERGE (f2:File {path: $neighbor_path})
                MERGE (f1)-[:NEIGHBOR]->(f2)
                """
                await session.run(
                    neighbor_query,
                    file_path=data["file_path"],
                    neighbor_path=neighbor_path,
                )

    async def consume(self) -> None:
        """Start consuming messages from AMQP."""
        if not self.amqp_connection:
            return

        channel = await self.amqp_connection.channel()

        # Declare exchange (idempotent operation)
        exchange = await channel.declare_exchange(
            AMQP_EXCHANGE,
            type="fanout",
            durable=True,
            auto_delete=False,
        )

        # Declare and bind queue
        queue = await channel.declare_queue(
            AMQP_QUEUE,
            durable=True,
            auto_delete=False,
        )
        await queue.bind(exchange, routing_key=AMQP_ROUTING_KEY)

        logger.info("📥 Starting to consume messages from queue: %s", AMQP_QUEUE)

        # Start consuming
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if not self._running:
                    break

                await self.process_message(message)


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def print_banner() -> None:
    """Print the Apollonia Populator banner."""
    banner = """
                 ____          _
 ___ ____  ___  / / /__  ___  (_)__ _
/ _ `/ _ \\/ _ \\/ / / _ \\/ _ \\/ / _ `/
\\_,_/ .__/\\___/_/_/\\___/_//_/_/\\_,_/
   /_/___  ___  ___  __ __/ /__ _/ /____  ____
     / _ \\/ _ \\/ _ \\/ // / / _ `/ __/ _ \\/ __/
    / .__/\\___/ .__/\\_,_/_/\\_,_/\\__/\\___/_/
   /_/       /_/
"""
    print(banner)


async def async_main() -> None:
    """Run the populator service."""
    populator: Populator | None = None

    def signal_handler(signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("⚡ Received signal %s, shutting down gracefully", signum)
        if populator:
            populator.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        async with Populator() as populator:
            await populator.consume()
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupted by user")
    except Exception:
        logger.exception("💥 Fatal error in populator")
        sys.exit(1)


def main() -> None:
    """Entry point for the populator service."""
    setup_logging()
    print_banner()

    # Verify environment
    if not AMQP_CONNECTION:
        logger.error("❌ AMQP_CONNECTION_STRING environment variable not set")
        sys.exit(1)

    if not NEO4J_PASSWORD or NEO4J_PASSWORD == "password":  # noqa: S105 # nosec B105
        logger.warning("⚠️ Using default Neo4j password - please change in production")

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
