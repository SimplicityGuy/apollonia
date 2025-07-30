"""Health check endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, status
from sqlalchemy import text

from ..database import get_session
from ..utils.cache import get_cache

logger = logging.getLogger(__name__)
router = APIRouter()

# Application version - should match pyproject.toml
APP_VERSION = "0.1.0"


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "message": "🌟 Apollonia API is healthy!",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict[str, Any]:
    """Readiness check with dependency verification."""
    checks = {
        "api": "ok",
        "database": "unknown",
        "cache": "unknown",
    }
    errors = []

    # Check database
    try:
        async for session in get_session():
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                checks["database"] = "ok"
            break
    except Exception as e:
        checks["database"] = "error"
        errors.append(f"Database: {e!s}")
        logger.error("❌ Database health check failed: %s", e)

    # Check cache
    try:
        redis = await get_cache()
        if await redis.ping():
            checks["cache"] = "ok"
    except Exception as e:
        checks["cache"] = "error"
        errors.append(f"Cache: {e!s}")
        logger.error("❌ Cache health check failed: %s", e)

    # Determine overall status
    all_ok = all(status == "ok" for status in checks.values())

    response: dict[str, Any] = {
        "status": "ready" if all_ok else "not ready",
        "checks": checks,
    }

    if errors:
        response["errors"] = errors

    if all_ok:
        return response
    else:
        return response
