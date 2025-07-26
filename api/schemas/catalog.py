"""Catalog schema definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogBase(BaseModel):
    """Base catalog schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class CatalogCreate(CatalogBase):
    """Schema for creating a catalog."""

    pass


class CatalogUpdate(BaseModel):
    """Schema for updating a catalog."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    settings: dict[str, Any] | None = None


class CatalogResponse(CatalogBase):
    """Schema for catalog response."""

    id: UUID
    user_id: str
    media_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class MediaFileBase(BaseModel):
    """Base media file schema."""

    file_name: str
    file_size: int
    media_type: str
    mime_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MediaFileResponse(MediaFileBase):
    """Schema for media file response."""

    id: UUID
    catalog_id: UUID
    file_path: str
    hash_sha256: str | None = None
    hash_xxh128: str | None = None
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
