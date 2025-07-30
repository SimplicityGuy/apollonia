"""ML Analyzer service for processing media files with machine learning models."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson
from aio_pika import ExchangeType, Message, connect_robust

from .models import ModelManager
from .processors import AudioProcessor, VideoProcessor

if TYPE_CHECKING:
    from aio_pika.abc import (
        AbstractIncomingMessage,
        AbstractRobustChannel,
        AbstractRobustConnection,
    )

logger = logging.getLogger(__name__)

# Configuration
AMQP_CONNECTION = os.getenv("AMQP_CONNECTION_STRING", "amqp://apollonia:apollonia@localhost:5672/")
AMQP_EXCHANGE_IN = "apollonia"
AMQP_EXCHANGE_OUT = "apollonia-enriched"
AMQP_QUEUE = "apollonia-analyzer"

# Redis configuration for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Model configuration
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/models")
ENABLE_GPU = os.getenv("ENABLE_GPU", "false").lower() == "true"


class MLAnalyzer:
    """ML analysis service that processes media files."""

    def __init__(self) -> None:
        """Initialize the ML analyzer."""
        self.amqp_connection: AbstractRobustConnection | None = None
        self.amqp_channel: AbstractRobustChannel | None = None
        self.model_manager = ModelManager(cache_dir=Path(MODEL_CACHE_DIR))
        self.audio_processor = AudioProcessor(self.model_manager)
        self.video_processor = VideoProcessor(self.model_manager)
        self._running = True

    async def __aenter__(self) -> MLAnalyzer:
        """Set up connections and initialize models."""
        logger.info("🔌 Connecting to AMQP broker at %s", AMQP_CONNECTION)
        self.amqp_connection = await connect_robust(AMQP_CONNECTION)
        self.amqp_channel = await self.amqp_connection.channel()  # type: ignore[assignment]

        # Declare exchanges
        if self.amqp_channel:
            await self.amqp_channel.declare_exchange(
                AMQP_EXCHANGE_IN,
                ExchangeType.TOPIC,
                durable=True,
            )

            await self.amqp_channel.declare_exchange(
                AMQP_EXCHANGE_OUT,
                ExchangeType.TOPIC,
                durable=True,
            )

            # Declare and bind queue
            queue = await self.amqp_channel.declare_queue(AMQP_QUEUE, durable=True)
            await queue.bind(AMQP_EXCHANGE_IN, routing_key="media.#")

        logger.info("📡 AMQP setup complete")

        # Initialize models
        logger.info("🧠 Initializing ML models...")
        await self.model_manager.initialize()
        logger.info("✅ ML models ready")

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Clean up connections."""
        if self.amqp_connection:
            logger.info("🔌 Closing AMQP connection")
            await self.amqp_connection.close()

    def stop(self) -> None:
        """Signal the analyzer to stop."""
        logger.info("🛑 Stopping ML analyzer")
        self._running = False

    async def process_message(self, message: AbstractIncomingMessage) -> None:
        """Process a single message from the queue.

        Args:
            message: Incoming AMQP message
        """
        async with message.process():
            try:
                # Parse message
                data = orjson.loads(message.body)
                file_path = Path(data["file_path"])
                media_type = data.get("media_metadata", {}).get("media_type", "unknown")

                logger.info("🔍 Processing %s file: %s", media_type, file_path.name)

                # Process based on media type
                ml_results: dict[str, Any] = {}

                if media_type == "audio":
                    ml_results = await self.audio_processor.process(file_path, data)
                elif media_type == "video":
                    ml_results = await self.video_processor.process(file_path, data)
                else:
                    logger.warning("⚠️ Unsupported media type: %s", media_type)
                    return

                # Enrich original data with ML results
                enriched_data = {**data, "ml_analysis": ml_results}

                # Publish enriched data
                if self.amqp_channel:
                    routing_key = f"enriched.{media_type}.analyzed"
                    exchange = await self.amqp_channel.get_exchange(AMQP_EXCHANGE_OUT)
                    await exchange.publish(
                        Message(
                            body=orjson.dumps(enriched_data),
                            content_type="application/json",
                            delivery_mode=2,  # Persistent
                        ),
                        routing_key=routing_key,
                    )
                    logger.info("📤 Published enriched data for: %s", file_path.name)

            except Exception:
                logger.exception("🚨 Error processing message")
                # Message will be requeued due to process() context

    async def consume(self) -> None:
        """Consume messages from the queue."""
        if not self.amqp_channel:
            raise RuntimeError("AMQP channel not initialized")

        queue = await self.amqp_channel.get_queue(AMQP_QUEUE)

        logger.info("🎧 Starting message consumption from queue: %s", AMQP_QUEUE)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if not self._running:
                    break

                await self.process_message(message)


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
    """Print the ML Analyzer banner."""
    banner = r"""
                 ____          _                            __
 ___ ____  ___  / / /__  ___  (_)__ _  ___ ____  ___ _/ /_ _____ ___ ____
/ _ `/ _ \/ _ \/ / / _ \/ _ \/ / _ `/ / _ `/ _ \/ _ `/ / // /_ // -_) __/
\_,_/ .__/\___/_/_/\___/_//_/_/\_,_/  \_,_/_//_/\_,_/_/\_, //__/\__/_/
   /_/                                                 /___/
                🧠 ML Analysis Service 🎵
"""
    print(banner)


async def async_main() -> None:
    """Run the ML analyzer service."""
    analyzer: MLAnalyzer | None = None

    def signal_handler(signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("⚡ Received signal %s, shutting down gracefully", signum)
        if analyzer:
            analyzer.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        async with MLAnalyzer() as analyzer:
            await analyzer.consume()
    except KeyboardInterrupt:
        logger.info("⌨️ Interrupted by user")
    except Exception:
        logger.exception("💥 Fatal error in ML analyzer")
        sys.exit(1)


def main() -> None:
    """Entry point for the ML analyzer service."""
    setup_logging()
    print_banner()

    # Verify environment
    if not AMQP_CONNECTION:
        logger.error("❌ AMQP_CONNECTION_STRING environment variable not set")
        sys.exit(1)

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
