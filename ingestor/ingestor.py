from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson
from asyncinotify import Inotify, Mask
from pika import BlockingConnection, DeliveryMode, URLParameters
from pika.spec import BasicProperties

from .prospector import Prospector

if TYPE_CHECKING:
    from pika.channel import Channel

logger = logging.getLogger(__name__)

AMQP_CONNECTION = os.getenv("AMQP_CONNECTION_STRING", "amqp://guest:guest@localhost:5672/")
AMQP_EXCHANGE = "apollonia"
DATA_DIRECTORY = os.getenv("DATA_DIRECTORY", "/data")
ROUTING_KEY = "file.created"


class Ingestor:
    """File monitoring service that publishes file events to AMQP."""

    def __init__(self) -> None:
        """Initialize the ingestor."""
        self.amqp_connection: BlockingConnection | None = None
        self.amqp_channel: Channel | None = None
        self.amqp_properties = BasicProperties(
            content_encoding="application/json",
            delivery_mode=DeliveryMode.Persistent,
        )
        self._running = True

    def __enter__(self) -> Ingestor:
        """Set up AMQP connection and channel."""
        logger.info("🔌 Connecting to AMQP broker at %s", AMQP_CONNECTION)
        self.amqp_connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
        self.amqp_channel = self.amqp_connection.channel()

        # Create the exchange to send the messages to.
        self.amqp_channel.exchange_declare(
            exchange=AMQP_EXCHANGE,
            exchange_type="fanout",
            durable=True,
            auto_delete=False,
        )
        logger.info("📡 AMQP exchange '%s' declared", AMQP_EXCHANGE)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Clean up AMQP connection."""
        if self.amqp_connection and not self.amqp_connection.is_closed:
            logger.info("🔌 Closing AMQP connection")
            self.amqp_connection.close()

    def stop(self) -> None:
        """Signal the ingestor to stop."""
        logger.info("🛑 Stopping ingestor")
        self._running = False

    async def ingest(self) -> None:
        """Monitor directory for file changes and publish to AMQP."""
        logger.info("👁️ Starting file monitoring on %s", DATA_DIRECTORY)

        # Ensure the data directory exists
        Path(DATA_DIRECTORY).mkdir(parents=True, exist_ok=True)

        async with Inotify() as inotify:
            inotify.add_watch(DATA_DIRECTORY, Mask.CREATE | Mask.MOVED_TO | Mask.CLOSE_WRITE)

            async for event in inotify:
                if not self._running:
                    break

                try:
                    logger.debug("🔍 Processing event: %s for %s", event.mask, event.path)
                    prospector = Prospector(event.path)
                    data = await prospector.prospect()

                    if self.amqp_channel:
                        message_body = orjson.dumps(
                            data,
                            option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2,
                        )
                        self.amqp_channel.basic_publish(
                            exchange=AMQP_EXCHANGE,
                            routing_key=ROUTING_KEY,
                            body=message_body,
                            properties=self.amqp_properties,
                        )
                        logger.info("📤 Published event for file: %s", event.path)
                except Exception:
                    logger.exception("💥 Error processing file event for %s", event.path)


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
    """Print the Apollonia Ingestor banner."""
    banner = r"""
                 ____          _
 ___ ____  ___  / / /__  ___  (_)__ _
/ _ `/ _ \/ _ \/ / / _ \/ _ \/ / _ `/
\_,_/ .__/\___/_/_/\___/_//_/_/\_,_/
   /_/(_)__  ___ ____ ___ / /____  ____
     / / _ \/ _ `/ -_|_-</ __/ _ \/ __/
    /_/_//_/\_, /\__/___/\__/\___/_/
           /___/
"""
    print(banner)


async def async_main() -> None:
    """Run the ingestor service."""
    ingestor: Ingestor | None = None

    def signal_handler(signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("⚡ Received signal %s, shutting down gracefully", signum)
        if ingestor:
            ingestor.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        with Ingestor() as ingestor:
            await ingestor.ingest()
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupted by user")
    except Exception:
        logger.exception("💥 Fatal error in ingestor")
        sys.exit(1)


def main() -> None:
    """Entry point for the ingestor service."""
    setup_logging()
    print_banner()

    # Verify environment
    if not AMQP_CONNECTION:
        logger.error("❌ AMQP_CONNECTION_STRING environment variable not set")
        sys.exit(1)

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
