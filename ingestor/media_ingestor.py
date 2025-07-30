"""Enhanced ingestor for media files with multi-directory support."""

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

from .media_prospector import MediaProspector
from .media_utils import MediaFileDetector

if TYPE_CHECKING:
    from pika.channel import Channel

logger = logging.getLogger(__name__)

# Configuration
AMQP_CONNECTION = os.getenv("AMQP_CONNECTION_STRING", "amqp://apollonia:apollonia@localhost:5672/")
AMQP_EXCHANGE = "apollonia"

# Support multiple watch directories via comma-separated list
WATCH_DIRECTORIES = os.getenv("WATCH_DIRECTORIES", "/data").split(",")

# Media-specific configuration
MEDIA_ONLY = os.getenv("MEDIA_ONLY", "true").lower() == "true"
WATCH_SUBDIRS = os.getenv("WATCH_SUBDIRS", "true").lower() == "true"


class MediaIngestor:
    """Enhanced file monitoring service for media files."""

    def __init__(self) -> None:
        """Initialize the media ingestor."""
        self.amqp_connection: BlockingConnection | None = None
        self.amqp_channel: Channel | None = None
        self.amqp_properties = BasicProperties(
            content_encoding="application/json",
            delivery_mode=DeliveryMode.Persistent,
        )
        self._running = True
        self.detector = MediaFileDetector()
        self.watch_dirs = [Path(d.strip()) for d in WATCH_DIRECTORIES]

    def __enter__(self) -> MediaIngestor:
        """Set up AMQP connection and channel."""
        logger.info("🔌 Connecting to AMQP broker at %s", AMQP_CONNECTION)
        self.amqp_connection = BlockingConnection(URLParameters(AMQP_CONNECTION))
        self.amqp_channel = self.amqp_connection.channel()

        # Create the exchange
        self.amqp_channel.exchange_declare(
            exchange=AMQP_EXCHANGE,
            exchange_type="topic",  # Use topic exchange for routing by media type
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
        logger.info("🛑 Stopping media ingestor")
        self._running = False

    def _add_directory_watches(self, observer: Any, base_dir: Path) -> None:
        """Recursively add watches to directories.

        Args:
            observer: Observer instance
            base_dir: Base directory to watch
        """
        # Create event handler
        event_handler = self._create_event_handler()

        # Add watch for base directory
        observer.schedule(event_handler, str(base_dir), recursive=WATCH_SUBDIRS)
        logger.debug("👁️ Watching directory: %s (recursive=%s)", base_dir, WATCH_SUBDIRS)

    async def _process_file_event(self, event_path: Path) -> None:
        """Process a file event.

        Args:
            event_path: Path of the file that triggered the event
        """
        # Skip if media-only mode and not a media file
        if MEDIA_ONLY and not self.detector.is_media_file(event_path):
            logger.debug("⏭️ Skipping non-media file: %s", event_path)
            return

        try:
            logger.info("🔍 Processing file: %s", event_path)
            prospector = MediaProspector(event_path)
            data = await prospector.prospect()

            if self.amqp_channel:
                routing_key = data.get("routing_key", "file.created")
                message_body = orjson.dumps(
                    data,
                    option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2,
                )

                self.amqp_channel.basic_publish(
                    exchange=AMQP_EXCHANGE,
                    routing_key=routing_key,
                    body=message_body,
                    properties=self.amqp_properties,
                )
                logger.info(
                    "📤 Published event for file: %s (routing: %s)", event_path.name, routing_key
                )
        except Exception:
            logger.exception("🚨 Error processing file event for %s", event_path)

    async def ingest(self) -> None:
        """Monitor directories for media files and publish to AMQP."""
        logger.info("🚀 Starting media file monitoring")
        logger.info("📁 Watch directories: %s", [str(d) for d in self.watch_dirs])
        logger.info("🎵 Media-only mode: %s", MEDIA_ONLY)
        logger.info("📂 Watch subdirectories: %s", WATCH_SUBDIRS)

        # Ensure watch directories exist
        for watch_dir in self.watch_dirs:
            watch_dir.mkdir(parents=True, exist_ok=True)

        # Create and start observer
        observer = Observer()

        # Add watches for all directories
        for watch_dir in self.watch_dirs:
            self._add_directory_watches(observer, watch_dir)

        observer.start()
        logger.info("✅ File monitoring active")

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

        class MediaIngestorEventHandler(FileSystemEventHandler):
            def __init__(self, ingestor: MediaIngestor) -> None:
                self.ingestor = ingestor
                self.loop = asyncio.get_event_loop()

            def on_created(self, event: Any) -> None:
                """Handle file/directory creation events."""
                if not event.is_directory:
                    self.loop.create_task(
                        self.ingestor._process_file_event(Path(str(event.src_path)))
                    )
                elif WATCH_SUBDIRS:
                    # Note: With recursive=True in watchdog, new dirs are auto-watched
                    logger.info("📁 New directory detected: %s", event.src_path)

            def on_moved(self, event: Any) -> None:
                """Handle file move events."""
                if not event.is_directory:
                    self.loop.create_task(
                        self.ingestor._process_file_event(Path(str(event.dest_path)))
                    )

            def on_modified(self, event: Any) -> None:
                """Handle file modification events."""
                if not event.is_directory:
                    self.loop.create_task(
                        self.ingestor._process_file_event(Path(str(event.src_path)))
                    )

        return MediaIngestorEventHandler(self)


def setup_logging() -> None:
    """Configure logging with emojis."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def print_banner() -> None:
    """Print the Media Ingestor banner."""
    banner = r"""
                 ____          _                 _ _
 ___ ____  ___  / / /__  ___  (_)__ _  __ _  ___ ___/ (_)__ _
/ _ `/ _ \/ _ \/ / / _ \/ _ \/ / _ `/ /  ' \/ -_) _  / / _ `/
\_,_/ .__/\___/_/_/\___/_//_/_/\_,_/ /_/_/_/\__/\_,_/_/\_,_/
   /_/  _                     __
  / ' \(_)__  ___ ____ ___ / /____  ____    🎵 Media Edition
 /_/_/_/ / _ \/ _ `/ -_|_-</ __/ _ \/ __/
      /_/_//_/\_, /\__/___/\__/\___/_/
             /___/
"""
    print(banner)


async def async_main() -> None:
    """Run the media ingestor service."""
    ingestor: MediaIngestor | None = None

    def signal_handler(signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("⚡ Received signal %s, shutting down gracefully", signum)
        if ingestor:
            ingestor.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        with MediaIngestor() as ingestor:
            await ingestor.ingest()
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupted by user")
    except Exception:
        logger.exception("💥 Fatal error in media ingestor")
        sys.exit(1)


def main() -> None:
    """Entry point for the media ingestor service."""
    setup_logging()
    print_banner()

    # Verify environment
    if not AMQP_CONNECTION:
        logger.error("❌ AMQP_CONNECTION_STRING environment variable not set")
        sys.exit(1)

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
