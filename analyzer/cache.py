"""Caching system for ML models and predictions."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import orjson
import redis.asyncio as redis

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for ML models and predictions."""

    def __init__(self, redis_url: str, ttl: int = 3600) -> None:
        """Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            ttl: Default time-to-live for cache entries in seconds
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis_client: redis.Redis | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._connected:
            return

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding/decoding
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("📦 Connected to Redis cache at %s", self.redis_url)
        except Exception as e:
            logger.warning("⚠️ Failed to connect to Redis: %s. Caching disabled.", e)
            self.redis_client = None
            self._connected = False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client and self._connected:
            await self.redis_client.close()
            self._connected = False
            logger.info("📦 Disconnected from Redis cache")

    def _make_key(self, namespace: str, identifier: str) -> str:
        """Create a cache key.

        Args:
            namespace: Cache namespace (e.g., "predictions", "features")
            identifier: Unique identifier within namespace

        Returns:
            Cache key string
        """
        return f"apollonia:{namespace}:{identifier}"

    async def get_prediction(self, file_hash: str, model_type: str) -> dict[str, Any] | None:
        """Get cached prediction for a file.

        Args:
            file_hash: SHA256 hash of the file
            model_type: Type of model prediction (e.g., "genre", "mood")

        Returns:
            Cached prediction or None if not found
        """
        if not self._connected or not self.redis_client:
            return None

        key = self._make_key("predictions", f"{file_hash}:{model_type}")

        try:
            data = await self.redis_client.get(key)
            if data:
                logger.debug("🎯 Cache hit for %s:%s", file_hash[:8], model_type)
                return dict(orjson.loads(data))
        except Exception as e:
            logger.warning("⚠️ Cache get error: %s", e)

        return None

    async def set_prediction(
        self, file_hash: str, model_type: str, prediction: dict[str, Any]
    ) -> None:
        """Cache a prediction for a file.

        Args:
            file_hash: SHA256 hash of the file
            model_type: Type of model prediction
            prediction: Prediction data to cache
        """
        if not self._connected or not self.redis_client:
            return

        key = self._make_key("predictions", f"{file_hash}:{model_type}")

        try:
            data = orjson.dumps(prediction)
            await self.redis_client.setex(key, self.ttl, data)
            logger.debug("💾 Cached prediction for %s:%s", file_hash[:8], model_type)
        except Exception as e:
            logger.warning("⚠️ Cache set error: %s", e)

    async def get_features(self, file_hash: str) -> dict[str, Any] | None:
        """Get cached features for a file.

        Args:
            file_hash: SHA256 hash of the file

        Returns:
            Cached features or None if not found
        """
        if not self._connected or not self.redis_client:
            return None

        key = self._make_key("features", file_hash)

        try:
            data = await self.redis_client.get(key)
            if data:
                logger.debug("🎯 Cache hit for features: %s", file_hash[:8])
                return dict(orjson.loads(data))
        except Exception as e:
            logger.warning("⚠️ Cache get error: %s", e)

        return None

    async def set_features(self, file_hash: str, features: dict[str, Any]) -> None:
        """Cache features for a file.

        Args:
            file_hash: SHA256 hash of the file
            features: Feature data to cache
        """
        if not self._connected or not self.redis_client:
            return

        key = self._make_key("features", file_hash)

        try:
            data = orjson.dumps(features)
            # Features have longer TTL as they don't change
            await self.redis_client.setex(key, self.ttl * 24, data)  # 24 hours
            logger.debug("💾 Cached features for %s", file_hash[:8])
        except Exception as e:
            logger.warning("⚠️ Cache set error: %s", e)

    async def get_model_metadata(self, model_name: str) -> dict[str, Any] | None:
        """Get cached model metadata.

        Args:
            model_name: Name of the model

        Returns:
            Cached metadata or None if not found
        """
        if not self._connected or not self.redis_client:
            return None

        key = self._make_key("models", model_name)

        try:
            data = await self.redis_client.get(key)
            if data:
                return dict(orjson.loads(data))
        except Exception as e:
            logger.warning("⚠️ Cache get error: %s", e)

        return None

    async def set_model_metadata(self, model_name: str, metadata: dict[str, Any]) -> None:
        """Cache model metadata.

        Args:
            model_name: Name of the model
            metadata: Model metadata to cache
        """
        if not self._connected or not self.redis_client:
            return

        key = self._make_key("models", model_name)

        try:
            data = orjson.dumps(metadata)
            # Model metadata has very long TTL
            await self.redis_client.setex(key, self.ttl * 168, data)  # 1 week
            logger.debug("💾 Cached model metadata for %s", model_name)
        except Exception as e:
            logger.warning("⚠️ Cache set error: %s", e)

    async def invalidate_file(self, file_hash: str) -> None:
        """Invalidate all cache entries for a file.

        Args:
            file_hash: SHA256 hash of the file
        """
        if not self._connected or not self.redis_client:
            return

        try:
            # Find all keys for this file
            pattern = f"apollonia:*:{file_hash}*"
            cursor = 0
            keys_to_delete = []

            # Scan for matching keys
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
                if cursor == 0:
                    break

            # Delete keys
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
                logger.info(
                    "🗑️ Invalidated %d cache entries for %s", len(keys_to_delete), file_hash[:8]
                )
        except Exception as e:
            logger.warning("⚠️ Cache invalidation error: %s", e)

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._connected or not self.redis_client:
            return {"connected": False}

        try:
            info = await self.redis_client.info()
            stats = {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_keys": await self.redis_client.dbsize(),
                "hit_rate": info.get("keyspace_hits", 0)
                / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
            return stats
        except Exception as e:
            logger.warning("⚠️ Error getting cache stats: %s", e)
            return {"connected": False, "error": str(e)}


class PredictionCache:
    """High-level cache interface for ML predictions."""

    def __init__(self, cache_manager: CacheManager) -> None:
        """Initialize prediction cache.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }

    async def get_or_compute(
        self,
        file_path: Path,
        file_hash: str,
        compute_func: Any,
        cache_key: str,
    ) -> dict[str, Any]:
        """Get cached result or compute and cache it.

        Args:
            file_path: Path to the file
            file_hash: SHA256 hash of the file
            compute_func: Async function to compute result if not cached
            cache_key: Cache key suffix (e.g., "audio_features", "genre_prediction")

        Returns:
            Cached or computed result
        """
        # Try to get from cache
        if cache_key.endswith("_features"):
            cached = await self.cache_manager.get_features(file_hash)
        else:
            cached = await self.cache_manager.get_prediction(file_hash, cache_key)

        if cached is not None:
            self._metrics["hits"] += 1
            logger.info("🎯 Using cached %s for %s", cache_key, file_path.name)
            return cached

        # Compute if not cached
        self._metrics["misses"] += 1
        logger.info("🔍 Computing %s for %s", cache_key, file_path.name)

        start_time = time.time()
        try:
            result = await compute_func(file_path)
            compute_time = time.time() - start_time
            logger.info("⏱️ Computed %s in %.2fs", cache_key, compute_time)

            # Cache the result
            if cache_key.endswith("_features"):
                await self.cache_manager.set_features(file_hash, result)
            else:
                await self.cache_manager.set_prediction(file_hash, cache_key, result)

            return dict(result)
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error("🚨 Error computing %s: %s", cache_key, e)
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics.

        Returns:
            Dictionary with cache metrics
        """
        total = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = self._metrics["hits"] / max(total, 1)

        return {
            "hits": self._metrics["hits"],
            "misses": self._metrics["misses"],
            "errors": self._metrics["errors"],
            "total_requests": total,
            "hit_rate": round(hit_rate, 3),
        }
