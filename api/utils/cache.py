"""Redis cache utilities."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Redis | None = None


async def init_cache() -> None:
    """Initialize Redis cache connection."""
    global redis_client

    settings = get_settings()
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    # Test connection
    await redis_client.ping()
    logger.info("💾 Cache connection established")


async def close_cache() -> None:
    """Close Redis cache connection."""
    global redis_client

    if redis_client:
        await redis_client.close()
        logger.info("💾 Cache connection closed")


async def get_cache() -> Redis:
    """Get Redis client."""
    if not redis_client:
        raise RuntimeError("Cache not initialized")
    return redis_client


# Compatibility alias for tests
get_cache_client = get_cache


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    if not redis_client:
        return None

    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning("⚠️ Cache get error for key %s: %s", key, e)

    return None


async def cache_set(
    key: str,
    value: Any,
    ttl: int | None = None,
) -> bool:
    """Set value in cache."""
    if not redis_client:
        return False

    settings = get_settings()
    ttl = ttl or settings.redis_cache_ttl

    try:
        serialized = json.dumps(value)
        await redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning("⚠️ Cache set error for key %s: %s", key, e)
        return False


async def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    if not redis_client:
        return False

    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning("⚠️ Cache delete error for key %s: %s", key, e)
        return False


async def cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching pattern."""
    if not redis_client:
        return 0

    try:
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await redis_client.delete(*keys)
            logger.info(
                "🗑️ Invalidated %d cache keys matching pattern: %s", deleted, pattern
            )
            return int(deleted)

        return 0
    except Exception as e:
        logger.warning("⚠️ Cache invalidation error for pattern %s: %s", pattern, e)
        return 0
