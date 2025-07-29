from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson
from pika import BlockingConnection, DeliveryMode, URLParameters
from pika.spec import BasicProperties
from watchdog.events import (
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from .prospector import Prospector

if TYPE_CHECKING:
    from pika.channel import Channel

logger = logging.getLogger(__name__)

AMQP_CONNECTION = os.getenv("AMQP_CONNECTION_STRING", "amqp://apollonia:apollonia@localhost:5672/")
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

        # Create event handler
        event_handler = self._create_event_handler()

        # Create and start observer
        observer = Observer()
        observer.schedule(event_handler, DATA_DIRECTORY, recursive=False)
        observer.start()

        try:
            # Keep running until stopped
            stop_event = asyncio.Event()
            while self._running:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.1)
                except TimeoutError:
                    continue
        finally:
            observer.stop()
            observer.join()

    def _create_event_handler(self) -> FileSystemEventHandler:
        """Create a file system event handler."""

        class IngestorEventHandler(FileSystemEventHandler):
            def __init__(self, ingestor: Ingestor) -> None:
                self.ingestor = ingestor
                self.loop = asyncio.get_event_loop()
                # Track recently processed files to avoid duplicates
                self._recent_files: dict[str, float] = {}
                self._cleanup_interval = 5.0  # seconds

            def on_created(self, event: Any) -> None:
                """Handle file creation events."""
                if not event.is_directory:
                    self.loop.create_task(self._process_file(str(event.src_path), "IN_CREATE"))

            def on_modified(self, event: Any) -> None:
                """Handle file modification events."""
                if not event.is_directory:
                    # Only process modifications after a longer delay to avoid duplicates
                    self.loop.create_task(
                        self._process_file(str(event.src_path), "IN_MODIFY", delay=1.0)
                    )

            def on_moved(self, event: Any) -> None:
                """Handle file move events."""
                if not event.is_directory:
                    self.loop.create_task(self._process_file(str(event.dest_path), "IN_MOVED"))

            async def _process_file(
                self, file_path: str, event_type: str = "IN_CREATE", delay: float = 0
            ) -> None:
                """Process a file event."""
                # Apply delay if specified
                if delay > 0:
                    await asyncio.sleep(delay)

                try:
                    # Check if we've recently processed this file
                    current_time = asyncio.get_event_loop().time()
                    if file_path in self._recent_files:
                        last_processed = self._recent_files[file_path]
                        # 0.5 second debounce - enough to prevent duplicates but allow tests to run
                        if current_time - last_processed < 0.5:
                            logger.debug("⏭️ Skipping duplicate event for %s", file_path)
                            return

                    # Record this file as processed
                    self._recent_files[file_path] = current_time

                    # Clean up old entries
                    if len(self._recent_files) > 100:
                        cutoff_time = current_time - self._cleanup_interval
                        self._recent_files = {
                            path: time
                            for path, time in self._recent_files.items()
                            if time > cutoff_time
                        }

                    logger.info("🔍 Processing %s event for %s", event_type, file_path)
                    prospector = Prospector(Path(file_path))
                    data = await prospector.prospect()
                    # Override event type with the actual event
                    data["event_type"] = event_type

                    if self.ingestor.amqp_channel:
                        message_body = orjson.dumps(
                            data,
                            option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2,
                        )
                        logger.debug("📝 Message data: %s", data)
                        self.ingestor.amqp_channel.basic_publish(
                            exchange=AMQP_EXCHANGE,
                            routing_key=ROUTING_KEY,
                            body=message_body,
                            properties=self.ingestor.amqp_properties,
                        )
                        logger.info("📤 Published %s event for file: %s", event_type, file_path)
                    else:
                        logger.error("❌ No AMQP channel available to publish message")
                except Exception:
                    logger.exception("💥 Error processing file event for %s", file_path)

        return IngestorEventHandler(self)


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
