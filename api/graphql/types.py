"""GraphQL type definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import strawberry
from strawberry import field

# Define JSON scalar type for GraphQL
JSON = strawberry.scalar(
    Any,
    name="JSON",
    description="The `JSON` scalar type represents JSON values.",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


@strawberry.type
class Catalog:
    """Catalog GraphQL type."""

    id: UUID
    user_id: str
    name: str
    description: str | None
    media_count: int
    settings: JSON
    created_at: datetime
    updated_at: datetime

    @field
    async def media_files(
        self,
        first: int = 20,
        after: str | None = None,
    ) -> MediaFileConnection:
        """Get media files in this catalog."""
        # TODO: Implement
        return MediaFileConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            total_count=0,
        )


@strawberry.type
class MediaFile:
    """Media file GraphQL type."""

    id: UUID
    catalog_id: UUID
    file_path: str
    file_name: str
    file_size: int
    media_type: str
    mime_type: str | None
    hash_sha256: str | None
    hash_xxh128: str | None
    metadata: JSON
    status: str
    created_at: datetime
    updated_at: datetime

    @field
    async def catalog(self) -> Catalog | None:
        """Get the catalog this file belongs to."""
        # TODO: Implement
        return None

    @field
    async def analysis(self) -> MediaAnalysis | None:
        """Get ML analysis results."""
        # TODO: Implement
        return None


@strawberry.type
class MediaAnalysis:
    """Media analysis GraphQL type."""

    id: UUID
    media_file_id: UUID
    status: str
    results: JSON
    error: str | None
    created_at: datetime
    updated_at: datetime

    @field
    async def media_file(self) -> MediaFile | None:
        """Get the media file this analysis belongs to."""
        # TODO: Implement
        return None


@strawberry.type
class PageInfo:
    """Pagination info."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None


@strawberry.type
class CatalogEdge:
    """Catalog edge for pagination."""

    cursor: str
    node: Catalog


@strawberry.type
class CatalogConnection:
    """Catalog connection for pagination."""

    edges: list[CatalogEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class MediaFileEdge:
    """Media file edge for pagination."""

    cursor: str
    node: MediaFile


@strawberry.type
class MediaFileConnection:
    """Media file connection for pagination."""

    edges: list[MediaFileEdge]
    page_info: PageInfo
    total_count: int


@strawberry.input
class SearchInput:
    """Search input type."""

    query: str | None = None
    catalog_ids: list[UUID] | None = None
    media_types: list[str] | None = None
    genres: list[str] | None = None
    moods: list[str] | None = None
    min_size: int | None = None
    max_size: int | None = None
    min_tempo: float | None = None
    max_tempo: float | None = None
    page: int = 1
    size: int = 20
    sort_by: str = "created"


@strawberry.type
class SearchResultItem:
    """Search result item."""

    id: UUID
    catalog_id: UUID
    file_name: str
    file_size: int
    media_type: str
    mime_type: str | None
    created_at: datetime
    updated_at: datetime
    metadata: JSON
    analysis: JSON | None


@strawberry.type
class SearchResult:
    """Search result type."""

    results: list[SearchResultItem]
    total: int
    page: int
    size: int
    pages: int
