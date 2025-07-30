"""GraphQL type definitions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import strawberry
from strawberry import field
from strawberry.scalars import JSON as StrawberryJSON

# For type checking, use Any; at runtime, use the Strawberry JSON scalar
if TYPE_CHECKING:
    JSON = Any
else:
    JSON = StrawberryJSON


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

    # Aliases for test compatibility
    @property
    def filename(self) -> str:
        """Alias for file_name."""
        return self.file_name

    @property
    def size(self) -> int:
        """Alias for file_size."""
        return self.file_size

    @property
    def fileName(self) -> str:
        """GraphQL field alias for file_name."""
        return self.file_name

    @property
    def filePath(self) -> str:
        """GraphQL field alias for file_path."""
        return self.file_path

    @property
    def fileSize(self) -> int:
        """GraphQL field alias for file_size."""
        return self.file_size

    @property
    def mediaType(self) -> str:
        """GraphQL field alias for media_type."""
        return self.media_type

    @property
    def createdAt(self) -> datetime:
        """GraphQL field alias for created_at."""
        return self.created_at

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

    # Aliases for test compatibility
    @property
    def items(self) -> list[MediaFile]:
        """Alias for getting nodes from edges."""
        return [edge.node for edge in self.edges]

    @property
    def total(self) -> int:
        """Alias for total_count."""
        return self.total_count


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
    score: float = 1.0  # Default score for search results

    # Aliases for test compatibility
    @property
    def filename(self) -> str:
        """Alias for file_name."""
        return self.file_name


@strawberry.type
class SearchResult:
    """Search result type."""

    results: list[SearchResultItem]
    total: int
    page: int
    size: int
    pages: int

    # Aliases for test compatibility
    @property
    def totalCount(self) -> int:
        """GraphQL field alias for total."""
        return self.total

    @property
    def facets(self) -> dict[str, Any]:
        """GraphQL field for facets."""
        # Return empty facets for now
        return {"mediaTypes": []}


@strawberry.input
class MediaFileInput:
    """Input type for creating media files."""

    path: str
    filename: str
    mediaType: str
    size: int
    catalogId: UUID | None = None
    metadata: JSON | None = None


@strawberry.input
class MediaFileUpdateInput:
    """Input type for updating media files."""

    filename: str | None = None
    size: int | None = None
    metadata: JSON | None = None
    status: str | None = None


@strawberry.type
class DeleteResult:
    """Result type for delete operations."""

    success: bool
    message: str
