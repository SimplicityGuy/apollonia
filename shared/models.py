"""Shared models for API compatibility.

This module provides API-specific views of the database models with
additional fields like created_at and updated_at for GraphQL/REST compatibility.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, UUID, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import Base


class TimestampMixin:
    """Mixin for API timestamp fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Catalog(Base, TimestampMixin):
    """Catalog model for API."""

    __tablename__ = "catalogs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    media_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class MediaFile(Base, TimestampMixin):
    """Media file model with API timestamp fields for compatibility."""

    __tablename__ = "media_files"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Add catalog relationship
    catalog_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # File identification
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    xxh128_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # File paths and names
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # API compatibility
    file_name: Mapped[str] = mapped_column(Text, nullable=False)  # API compatibility
    filename: Mapped[str] = mapped_column(Text, nullable=False)  # Database compatibility
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # File metadata
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # API compatibility
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # Database compatibility
    media_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # JSON metadata
    file_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata for API compatibility."""
        return self.file_metadata

    def set_metadata(self, value: dict[str, Any]) -> None:
        """Set metadata for API compatibility."""
        self.file_metadata = value


class MediaAnalysis(Base, TimestampMixin):
    """Media analysis results model."""

    __tablename__ = "media_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    results: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
