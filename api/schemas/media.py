"""Media file schema definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MediaAnalysisResponse(BaseModel):
    """Schema for media analysis response."""

    id: UUID
    media_file_id: UUID
    status: str
    results: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class MediaFileResponse(BaseModel):
    """Schema for media file response."""

    id: UUID
    catalog_id: UUID
    file_path: str
    file_name: str
    file_size: int
    media_type: str
    mime_type: str | None = None
    hash_sha256: str | None = None
    hash_xxh128: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class MediaFileUpdate(BaseModel):
    """Schema for media file update request."""

    file_size: int | None = None
    file_name: str | None = None
    media_type: str | None = None
    metadata: dict[str, Any] | None = None
    status: str | None = None
