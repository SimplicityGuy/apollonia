"""Enhanced ML Analyzer with caching and improved model management."""

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

from .cache import CacheManager, PredictionCache
from .model_management import EnhancedModelManager
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
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Model configuration
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/models")
ENABLE_GPU = os.getenv("ENABLE_GPU", "false").lower() == "true"
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"


class EnhancedMLAnalyzer:
    """Enhanced ML analysis service with caching and improved model management."""

    def __init__(self) -> None:
        """Initialize the enhanced ML analyzer."""
        self.amqp_connection: AbstractRobustConnection | None = None
        self.amqp_channel: AbstractRobustChannel | None = None

        # Caching setup
        self.cache_manager = CacheManager(REDIS_URL, ttl=CACHE_TTL) if ENABLE_CACHING else None
        self.prediction_cache = PredictionCache(self.cache_manager) if self.cache_manager else None

        # Model management
        self.model_manager = EnhancedModelManager(
            cache_dir=Path(MODEL_CACHE_DIR),
            cache_manager=self.cache_manager,
        )

        # Processors
        self.audio_processor = AudioProcessor(self.model_manager)  # type: ignore[arg-type]
        self.video_processor = VideoProcessor(self.model_manager)  # type: ignore[arg-type]

        self._running = True
        self._process_count = 0
        self._error_count = 0

    async def __aenter__(self) -> EnhancedMLAnalyzer:
        """Set up connections and initialize services."""
        # Connect to Redis cache
        if self.cache_manager:
            logger.info("📦 Connecting to Redis cache...")
            await self.cache_manager.connect()
            cache_stats = await self.cache_manager.get_stats()
            logger.info("📦 Cache stats: %s", cache_stats)

        # Connect to AMQP
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
        logger.info("🧠 Initializing ML models with enhanced management...")
        await self.model_manager.initialize()
        logger.info("✅ ML models ready")

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Clean up connections and resources."""
        # Log final stats
        logger.info(
            "📊 Final stats - Processed: %d, Errors: %d",
            self._process_count,
            self._error_count,
        )

        if self.prediction_cache:
            cache_metrics = self.prediction_cache.get_metrics()
            logger.info("📦 Cache metrics: %s", cache_metrics)

        model_metrics = self.model_manager.get_metrics()
        logger.info("🤖 Model metrics: %s", model_metrics)

        # Clean up connections
        if self.cache_manager:
            await self.cache_manager.disconnect()

        if self.amqp_connection:
            logger.info("🔌 Closing AMQP connection")
            await self.amqp_connection.close()

    def stop(self) -> None:
        """Signal the analyzer to stop."""
        logger.info("🛑 Stopping enhanced ML analyzer")
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
                file_hash = data.get("sha256_hash", "")
                media_type = data.get("media_metadata", {}).get("media_type", "unknown")

                logger.info(
                    "🔍 Processing %s file: %s (hash: %s)",
                    media_type,
                    file_path.name,
                    file_hash[:8],
                )

                # Process based on media type
                ml_results: dict[str, Any] = {}

                if media_type == "audio":
                    if self.prediction_cache and file_hash:
                        # Use caching for audio processing
                        ml_results = await self.prediction_cache.get_or_compute(
                            file_path,
                            file_hash,
                            lambda fp: self.audio_processor.process(fp, data),
                            "audio_analysis",
                        )
                    else:
                        ml_results = await self.audio_processor.process(file_path, data)

                elif media_type == "video":
                    if self.prediction_cache and file_hash:
                        # Use caching for video processing
                        ml_results = await self.prediction_cache.get_or_compute(
                            file_path,
                            file_hash,
                            lambda fp: self.video_processor.process(fp, data),
                            "video_analysis",
                        )
                    else:
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

                self._process_count += 1

                # Log periodic stats
                if self._process_count % 100 == 0:
                    await self._log_performance_stats()

            except Exception:
                logger.exception("🚨 Error processing message")
                self._error_count += 1
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

    async def _log_performance_stats(self) -> None:
        """Log performance statistics."""
        stats: dict[str, Any] = {
            "processed": self._process_count,
            "errors": self._error_count,
            "error_rate": round(self._error_count / max(self._process_count, 1), 3),
        }

        if self.cache_manager:
            cache_stats = await self.cache_manager.get_stats()
            stats["cache"] = cache_stats

        if self.prediction_cache:
            stats["predictions"] = self.prediction_cache.get_metrics()

        stats["models"] = self.model_manager.get_metrics()

        logger.info("📊 Performance stats: %s", stats)

    async def update_models(self) -> None:
        """Check for and apply model updates."""
        logger.info("🔄 Checking for model updates...")
        update_results = await self.model_manager.update_models()
        logger.info("🔄 Model update results: %s", update_results)

    async def cleanup(self) -> None:
        """Perform cleanup operations."""
        logger.info("🧹 Running cleanup operations...")
        await self.model_manager.cleanup()
        logger.info("✅ Cleanup complete")


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
    """Print the Enhanced ML Analyzer banner."""
    banner = r"""
                 ____          _                            __
 ___ ____  ___  / / /__  ___  (_)__ _  ___ ____  ___ _/ /_ _____ ___ ____
/ _ `/ _ \/ _ \/ / / _ \/ _ \/ / _ `/ / _ `/ _ \/ _ `/ / // /_ // -_) __/
\_,_/ .__/\___/_/_/\___/_//_/_/\_,_/  \_,_/_//_/\_,_/_/\_, //__/\__/_/
   /_/                                                 /___/
        🧠 Enhanced ML Analysis Service with Caching 📦
"""
    print(banner)


async def async_main() -> None:
    """Run the enhanced ML analyzer service."""
    analyzer: EnhancedMLAnalyzer | None = None

    def signal_handler(signum: int, _frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("⚡ Received signal %s, shutting down gracefully", signum)
        if analyzer:
            analyzer.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print_banner()
    setup_logging()

    try:
        async with EnhancedMLAnalyzer() as analyzer:
            # Run periodic tasks
            async def periodic_tasks() -> None:
                while analyzer._running:
                    # Check for model updates every hour
                    await asyncio.sleep(3600)
                    if analyzer._running:
                        await analyzer.update_models()

            # Run cleanup every 24 hours
            async def cleanup_task() -> None:
                while analyzer._running:
                    await asyncio.sleep(86400)
                    if analyzer._running:
                        await analyzer.cleanup()

            # Start background tasks
            tasks = [
                asyncio.create_task(analyzer.consume()),
                asyncio.create_task(periodic_tasks()),
                asyncio.create_task(cleanup_task()),
            ]

            # Wait for any task to complete
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Wait for cancellation
            await asyncio.gather(*pending, return_exceptions=True)

    except Exception:
        logger.exception("💥 Fatal error in enhanced analyzer")
        sys.exit(1)


def main() -> None:
    """Entry point for the enhanced analyzer."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
