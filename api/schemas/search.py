"""Search schema definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str | None = None
    catalog_ids: list[UUID] | None = None
    media_types: list[str] | None = None
    genres: list[str] | None = None
    moods: list[str] | None = None
    min_size: int | None = None
    max_size: int | None = None
    min_tempo: float | None = None
    max_tempo: float | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: str = "created"  # name, size, created, modified


class SearchResult(BaseModel):
    """Search result item."""

    id: UUID
    catalog_id: UUID
    file_name: str
    file_size: int
    media_type: str
    mime_type: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    """Search response schema."""

    results: list[SearchResult]
    total: int
    page: int
    size: int
    pages: int
