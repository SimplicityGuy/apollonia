"""Database connection and session management."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

logger = logging.getLogger(__name__)

# Global database objects
engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """Initialize database connection."""
    global engine, async_session_factory

    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        echo=settings.debug,
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Test connection
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)

    logger.info("📚 Database connection established")


async def close_db() -> None:
    """Close database connection."""
    global engine

    if engine:
        await engine.dispose()
        logger.info("📚 Database connection closed")


async def get_session() -> AsyncIterator[AsyncSession]:
    """Get database session."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Compatibility alias for tests expecting Neo4j
get_neo4j_session = get_session
