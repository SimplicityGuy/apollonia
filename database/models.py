"""SQLAlchemy models for media catalog database."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    UUID,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class MediaFile(Base):
    """Media file record with metadata and ML analysis results."""

    __tablename__ = "media_files"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File identification
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    xxh128_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # File paths
    original_path: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    extension: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # File metadata
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Timestamps
    file_created: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_accessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Processing timestamps
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Technical metadata (from file analysis)
    duration: Mapped[float | None] = mapped_column(Float)  # seconds
    bitrate: Mapped[int | None] = mapped_column(Integer)  # bits per second
    sample_rate: Mapped[int | None] = mapped_column(Integer)  # Hz
    channels: Mapped[int | None] = mapped_column(Integer)

    # Video-specific metadata
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    fps: Mapped[float | None] = mapped_column(Float)
    video_codec: Mapped[str | None] = mapped_column(String(50))
    audio_codec: Mapped[str | None] = mapped_column(String(50))
    has_audio: Mapped[bool | None] = mapped_column(Boolean)

    # Directory structure (for inferring artist/album)
    parent_dir: Mapped[str | None] = mapped_column(Text)
    grandparent_dir: Mapped[str | None] = mapped_column(Text)

    # Raw metadata storage
    file_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Relationships
    ml_predictions: Mapped[list[MLPrediction]] = relationship(
        "MLPrediction", back_populates="media_file", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("sha256_hash", "original_path", name="uq_file_hash_path"),
        Index("idx_media_type_status", "media_type", "status"),
        Index("idx_ingested_analyzed", "ingested_at", "analyzed_at"),
    )


class MLPrediction(Base):
    """ML prediction results for a media file."""

    __tablename__ = "ml_predictions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to media file
    media_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Prediction metadata
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Timestamps
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Prediction results (flexible JSON storage)
    predictions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Top predictions for quick querying
    top_labels: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    top_scores: Mapped[list[float] | None] = mapped_column(ARRAY(Float))

    # Relationships
    media_file: Mapped[MediaFile] = relationship("MediaFile", back_populates="ml_predictions")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "media_file_id", "model_name", "prediction_type", name="uq_file_model_prediction"
        ),
        Index("idx_prediction_type_labels", "prediction_type", "top_labels"),
    )


class Artist(Base):
    """Artist information extracted from metadata or inferred from paths."""

    __tablename__ = "artists"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Artist info
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    sort_name: Mapped[str | None] = mapped_column(Text)

    # External IDs
    musicbrainz_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    spotify_id: Mapped[str | None] = mapped_column(String(50), unique=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Additional metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Album(Base):
    """Album information extracted from metadata or inferred from paths."""

    __tablename__ = "albums"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Album info
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    artist_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    year: Mapped[int | None] = mapped_column(Integer)

    # External IDs
    musicbrainz_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    spotify_id: Mapped[str | None] = mapped_column(String(50), unique=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Additional metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Constraints
    __table_args__ = (
        UniqueConstraint("title", "artist_id", name="uq_album_artist"),
        Index("idx_album_year", "year"),
    )


class Genre(Base):
    """Genre taxonomy with hierarchical structure."""

    __tablename__ = "genres"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Genre info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    parent_genre: Mapped[str | None] = mapped_column(String(100), index=True)

    # Source info
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "discogs", "user"

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ProcessingQueue(Base):
    """Queue for tracking file processing status."""

    __tablename__ = "processing_queue"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File reference
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # Queue metadata
    queue_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Processing info
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Message data
    message_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Constraints
    __table_args__ = (
        Index("idx_queue_status_priority", "queue_name", "status", "priority"),
        Index("idx_queue_timestamps", "queued_at", "started_at", "completed_at"),
    )
