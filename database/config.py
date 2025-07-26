"""Database configuration and connection management."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Database configuration from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://apollonia:apollonia@localhost:5432/apollonia"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Get an async database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session() as session:
        yield session
