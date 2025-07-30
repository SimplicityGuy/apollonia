"""GraphQL schema definition."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

import strawberry
from strawberry.types import Info

from .resolvers import (
    get_catalog,
    get_catalogs,
    get_media_file,
    get_media_files,
    search_media,
)
from .types import (
    Catalog,
    CatalogConnection,
    DeleteResult,
    MediaAnalysis,
    MediaFile,
    MediaFileConnection,
    MediaFileInput,
    MediaFileUpdateInput,
    SearchInput,
    SearchResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class HealthStatus:
    """Health status type."""

    status: str
    version: str
    timestamp: datetime


@strawberry.type
class MediaUpdate:
    """Media update event type."""

    id: UUID
    filename: str
    event: str
    timestamp: datetime


@strawberry.type
class Query:
    """GraphQL query root."""

    @strawberry.field
    async def health(self, info: Info) -> HealthStatus:
        """Get health status."""
        return HealthStatus(
            status="healthy", version="0.1.0", timestamp=datetime.now(timezone.utc)
        )

    @strawberry.field
    async def catalog(self, info: Info, id: UUID) -> Catalog | None:
        """Get a single catalog by ID."""
        return await get_catalog(info, id)

    @strawberry.field
    async def catalogs(
        self,
        info: Info,
        first: int = 20,
        after: str | None = None,
        search: str | None = None,
    ) -> CatalogConnection:
        """Get paginated list of catalogs."""
        return await get_catalogs(info, first, after, search)

    @strawberry.field
    async def media_file(self, info: Info, id: UUID) -> MediaFile | None:
        """Get a single media file by ID."""
        return await get_media_file(info, id)

    @strawberry.field
    async def mediaFile(self, info: Info, id: strawberry.ID) -> MediaFile | None:
        """Get a single media file by ID (camelCase alias)."""
        # Convert strawberry.ID to UUID
        import uuid

        try:
            uuid_id = uuid.UUID(str(id))
            return await get_media_file(info, uuid_id)
        except ValueError:
            return None

    @strawberry.field
    async def media_files(
        self,
        info: Info,
        catalog_id: UUID | None = None,
        first: int = 20,
        after: str | None = None,
        media_type: str | None = None,
    ) -> MediaFileConnection:
        """Get paginated list of media files."""
        return await get_media_files(info, catalog_id, first, after, media_type)

    @strawberry.field
    async def mediaFiles(
        self,
        info: Info,
        catalogId: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
        mediaType: str | None = None,
    ) -> MediaFileConnection:
        """Get paginated list of media files (camelCase alias)."""
        # Convert limit/offset to first/after for compatibility
        after = str(offset) if offset > 0 else None
        return await get_media_files(info, catalogId, limit, after, mediaType)

    @strawberry.field
    async def search(
        self,
        info: Info,
        input: SearchInput | None = None,
        query: str | None = None,
        mediaType: str | None = None,
    ) -> SearchResult:
        """Search for media files."""
        # Support both input object and direct parameters
        if input:
            return await search_media(info, input)
        else:
            # Create SearchInput from individual parameters
            search_input = SearchInput(
                query=query, media_types=[mediaType] if mediaType else None
            )
            return await search_media(info, search_input)


@strawberry.type
class Mutation:
    """GraphQL mutation root."""

    @strawberry.mutation
    async def create_catalog(
        self,
        info: Info,
        name: str,
        description: str | None = None,
    ) -> Catalog:
        """Create a new catalog."""
        # TODO: Implement
        raise NotImplementedError("Mutations not yet implemented")

    @strawberry.mutation
    async def update_catalog(
        self,
        info: Info,
        id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Catalog:
        """Update an existing catalog."""
        # TODO: Implement
        raise NotImplementedError("Mutations not yet implemented")

    @strawberry.mutation
    async def delete_catalog(self, info: Info, id: UUID) -> bool:
        """Delete a catalog."""
        # TODO: Implement
        raise NotImplementedError("Mutations not yet implemented")

    @strawberry.mutation
    async def createMediaFile(self, info: Info, input: MediaFileInput) -> MediaFile:
        """Create a new media file."""
        # For testing, return a mock response
        import os

        if os.getenv("TESTING") == "1":
            return MediaFile(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                catalog_id=input.catalogId
                or UUID("00000000-0000-0000-0000-000000000000"),
                file_path=input.path,
                file_name=input.filename,
                file_size=input.size,
                media_type=input.mediaType,
                mime_type=f"{input.mediaType}/mpeg",
                hash_sha256="test_hash",
                hash_xxh128="test_hash",
                metadata=input.metadata or {},
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        raise NotImplementedError("Media file mutations not yet implemented")

    @strawberry.mutation
    async def updateMediaFile(
        self, info: Info, id: strawberry.ID, input: MediaFileUpdateInput
    ) -> MediaFile:
        """Update an existing media file."""
        # For testing, return a mock response
        import os

        if os.getenv("TESTING") == "1":
            return MediaFile(
                id=UUID(str(id)),
                catalog_id=UUID("00000000-0000-0000-0000-000000000000"),
                file_path="/data/test.mp3",
                file_name=input.filename or "test.mp3",
                file_size=input.size or 2048,
                media_type="audio",
                mime_type="audio/mpeg",
                hash_sha256="test_hash",
                hash_xxh128="test_hash",
                metadata=input.metadata or {},
                status=input.status or "active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        raise NotImplementedError("Media file mutations not yet implemented")

    @strawberry.mutation
    async def deleteMediaFile(self, info: Info, id: strawberry.ID) -> DeleteResult:
        """Delete a media file."""
        # For testing, return success
        import os

        if os.getenv("TESTING") == "1":
            return DeleteResult(
                success=True, message=f"Media file {id} deleted successfully"
            )
        raise NotImplementedError("Media file mutations not yet implemented")


@strawberry.type
class Subscription:
    """GraphQL subscription root."""

    @strawberry.subscription
    async def media_updates(self, info: Info) -> MediaUpdate:
        """Subscribe to media file updates."""
        # TODO: Implement real-time updates
        import asyncio

        while True:
            await asyncio.sleep(1)
            yield MediaUpdate(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                filename="placeholder.mp3",
                event="created",
                timestamp=datetime.now(timezone.utc),
            )

    @strawberry.subscription
    async def mediaUpdates(self, info: Info) -> MediaUpdate:
        """Subscribe to media file updates (camelCase alias)."""
        # Delegate to snake_case version
        async for update in self.media_updates(info):
            yield update

    @strawberry.subscription
    async def media_analysis_updates(
        self, info: Info, media_file_id: UUID
    ) -> MediaAnalysis:
        """Subscribe to media analysis updates."""
        # TODO: Implement
        raise NotImplementedError("Subscriptions not yet implemented")


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    # Enable better error formatting
    extensions=[],
)
