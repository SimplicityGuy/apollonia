"""GraphQL schema definition."""

from __future__ import annotations

import logging
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
    MediaAnalysis,
    MediaFile,
    MediaFileConnection,
    SearchInput,
    SearchResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class Query:
    """GraphQL query root."""

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
    async def search(self, info: Info, input: SearchInput) -> SearchResult:
        """Search for media files."""
        return await search_media(info, input)


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


@strawberry.type
class Subscription:
    """GraphQL subscription root."""

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
)
