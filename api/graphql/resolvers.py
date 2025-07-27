"""GraphQL resolver functions."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, or_, select

from ..database import get_session
from .types import (
    Catalog,
    CatalogConnection,
    CatalogEdge,
    MediaFile,
    MediaFileConnection,
    MediaFileEdge,
    PageInfo,
    SearchInput,
    SearchResult,
    SearchResultItem,
)

if TYPE_CHECKING:
    from strawberry.types import Info

logger = logging.getLogger(__name__)


def encode_cursor(value: str) -> str:
    """Encode cursor value."""
    return base64.b64encode(value.encode()).decode()


def decode_cursor(cursor: str) -> str:
    """Decode cursor value."""
    return base64.b64decode(cursor.encode()).decode()


async def get_catalog(info: Info, id: UUID) -> Catalog | None:
    """Get a single catalog by ID."""
    # Get current user from context
    user = info.context.get("user")
    if not user:
        return None

    async for session in get_session():
        from shared.models import Catalog as CatalogModel

        catalog = await session.get(CatalogModel, id)

        if not catalog or catalog.user_id != user.username:
            return None

        return Catalog(
            id=catalog.id,
            user_id=catalog.user_id,
            name=catalog.name,
            description=catalog.description,
            media_count=catalog.media_count,
            settings=catalog.settings,
            created_at=catalog.created_at,
            updated_at=catalog.updated_at,
        )

    return None


async def get_catalogs(
    info: Info,
    first: int,
    after: str | None,
    search: str | None,
) -> CatalogConnection:
    """Get paginated list of catalogs."""
    # Get current user from context
    user = info.context.get("user")
    if not user:
        return CatalogConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            total_count=0,
        )

    async for session in get_session():
        from shared.models import Catalog as CatalogModel

        # Build query
        query = select(CatalogModel).where(CatalogModel.user_id == user.username)

        if search:
            query = query.where(
                CatalogModel.name.ilike(f"%{search}%")
                | CatalogModel.description.ilike(f"%{search}%")
            )

        # Apply cursor
        if after:
            cursor_id = UUID(decode_cursor(after))
            query = query.where(CatalogModel.id > cursor_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query) or 0

        # Get results
        query = query.order_by(CatalogModel.id).limit(first + 1)
        result = await session.execute(query)
        catalogs = list(result.scalars())

        # Check if there are more results
        has_next = len(catalogs) > first
        if has_next:
            catalogs = catalogs[:-1]

        # Build edges
        edges = []
        for catalog in catalogs:
            edges.append(
                CatalogEdge(
                    cursor=encode_cursor(str(catalog.id)),
                    node=Catalog(
                        id=catalog.id,
                        user_id=catalog.user_id,
                        name=catalog.name,
                        description=catalog.description,
                        media_count=catalog.media_count,
                        settings=catalog.settings,
                        created_at=catalog.created_at,
                        updated_at=catalog.updated_at,
                    ),
                )
            )

        # Build page info
        page_info = PageInfo(
            has_next_page=has_next,
            has_previous_page=after is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return CatalogConnection(
            edges=edges,
            page_info=page_info,
            total_count=total,
        )

    # Should never reach here, but satisfy type checker
    return CatalogConnection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
        total_count=0,
    )


async def get_media_file(info: Info, id: UUID) -> MediaFile | None:
    """Get a single media file by ID."""
    # Get current user from context
    user = info.context.get("user")
    if not user:
        return None

    async for session in get_session():
        from shared.models import Catalog as CatalogModel
        from shared.models import MediaFile as MediaFileModel

        # Get media file with catalog
        result = await session.execute(
            select(MediaFileModel)
            .join(CatalogModel)
            .where(MediaFileModel.id == id, CatalogModel.user_id == user.username)
        )
        media_file = result.scalar_one_or_none()

        if not media_file:
            return None

        return MediaFile(
            id=media_file.id,
            catalog_id=media_file.catalog_id,
            file_path=media_file.file_path,
            file_name=media_file.file_name,
            file_size=media_file.file_size,
            media_type=media_file.media_type,
            mime_type=media_file.mime_type,
            hash_sha256=media_file.hash_sha256,
            hash_xxh128=media_file.hash_xxh128,
            metadata=media_file.metadata,
            status=media_file.status,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at,
        )

    return None


async def get_media_files(
    info: Info,
    catalog_id: UUID | None,
    first: int,
    after: str | None,
    media_type: str | None,
) -> MediaFileConnection:
    """Get paginated list of media files."""
    # Get current user from context
    user = info.context.get("user")
    if not user:
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

    async for session in get_session():
        from shared.models import Catalog as CatalogModel
        from shared.models import MediaFile as MediaFileModel

        # Build query
        query = (
            select(MediaFileModel)
            .join(CatalogModel)
            .where(CatalogModel.user_id == user.username)
        )

        if catalog_id:
            query = query.where(MediaFileModel.catalog_id == catalog_id)

        if media_type:
            query = query.where(MediaFileModel.media_type == media_type)

        # Apply cursor
        if after:
            cursor_id = UUID(decode_cursor(after))
            query = query.where(MediaFileModel.id > cursor_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query) or 0

        # Get results
        query = query.order_by(MediaFileModel.id).limit(first + 1)
        result = await session.execute(query)
        media_files = list(result.scalars())

        # Check if there are more results
        has_next = len(media_files) > first
        if has_next:
            media_files = media_files[:-1]

        # Build edges
        edges = []
        for media_file in media_files:
            edges.append(
                MediaFileEdge(
                    cursor=encode_cursor(str(media_file.id)),
                    node=MediaFile(
                        id=media_file.id,
                        catalog_id=media_file.catalog_id,
                        file_path=media_file.file_path,
                        file_name=media_file.file_name,
                        file_size=media_file.file_size,
                        media_type=media_file.media_type,
                        mime_type=media_file.mime_type,
                        hash_sha256=media_file.hash_sha256,
                        hash_xxh128=media_file.hash_xxh128,
                        metadata=media_file.metadata,
                        status=media_file.status,
                        created_at=media_file.created_at,
                        updated_at=media_file.updated_at,
                    ),
                )
            )

        # Build page info
        page_info = PageInfo(
            has_next_page=has_next,
            has_previous_page=after is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return MediaFileConnection(
            edges=edges,
            page_info=page_info,
            total_count=total,
        )

    # Should never reach here, but satisfy type checker
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


async def search_media(info: Info, input: SearchInput) -> SearchResult:
    """Search for media files."""
    # Get current user from context
    user = info.context.get("user")
    if not user:
        return SearchResult(
            results=[],
            total=0,
            page=input.page,
            size=input.size,
            pages=0,
        )

    async for session in get_session():
        from shared.models import (
            Catalog as CatalogModel,
        )
        from shared.models import (
            MediaAnalysis as MediaAnalysisModel,
        )
        from shared.models import (
            MediaFile as MediaFileModel,
        )

        # Base query
        query = (
            select(MediaFileModel, MediaAnalysisModel)
            .join(CatalogModel)
            .outerjoin(MediaAnalysisModel)
            .where(CatalogModel.user_id == user.username)
        )

        # Apply search filters
        if input.query:
            search_term = f"%{input.query}%"
            query = query.where(
                or_(
                    MediaFileModel.file_name.ilike(search_term),
                    MediaFileModel.metadata["tags"].astext.ilike(search_term),
                )
            )

        if input.catalog_ids:
            query = query.where(MediaFileModel.catalog_id.in_(input.catalog_ids))

        if input.media_types:
            query = query.where(MediaFileModel.media_type.in_(input.media_types))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query) or 0

        # Apply pagination
        offset = (input.page - 1) * input.size
        query = query.offset(offset).limit(input.size)

        # Execute query
        result = await session.execute(query)
        rows = result.all()

        # Build results
        results = []
        for media_file, analysis in rows:
            result_item = SearchResultItem(
                id=media_file.id,
                catalog_id=media_file.catalog_id,
                file_name=media_file.file_name,
                file_size=media_file.file_size,
                media_type=media_file.media_type,
                mime_type=media_file.mime_type,
                created_at=media_file.created_at,
                updated_at=media_file.updated_at,
                metadata=media_file.metadata,
                analysis=analysis.results if analysis else None,
            )
            results.append(result_item)

        # Calculate pages
        pages = (total + input.size - 1) // input.size if total > 0 else 0

        return SearchResult(
            results=results,
            total=total,
            page=input.page,
            size=input.size,
            pages=pages,
        )

    # Should never reach here, but satisfy type checker
    return SearchResult(
        results=[],
        total=0,
        page=input.page,
        size=input.size,
        pages=0,
    )
