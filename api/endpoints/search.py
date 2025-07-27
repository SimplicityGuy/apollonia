"""Search endpoints for media discovery."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..endpoints.auth import User, get_current_active_user
from ..schemas.search import SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_media(
    search_request: SearchRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Search for media files across catalogs."""
    logger.info("🔍 Searching media with query: %s", search_request.query)

    from shared.models import Catalog, MediaAnalysis, MediaFile

    # Base query - only user's catalogs
    query = (
        select(MediaFile, MediaAnalysis)
        .join(Catalog)
        .outerjoin(MediaAnalysis)
        .where(Catalog.user_id == current_user.username)
    )

    # Apply search filters
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.where(
            or_(
                MediaFile.file_name.ilike(search_term),
                MediaFile.metadata["tags"].astext.ilike(search_term),
                MediaAnalysis.results["predictions"]["genres"].astext.ilike(
                    search_term
                ),
            )
        )

    # Filter by catalog
    if search_request.catalog_ids:
        query = query.where(MediaFile.catalog_id.in_(search_request.catalog_ids))

    # Filter by media type
    if search_request.media_types:
        query = query.where(MediaFile.media_type.in_(search_request.media_types))

    # Filter by file size
    if search_request.min_size:
        query = query.where(MediaFile.file_size >= search_request.min_size)
    if search_request.max_size:
        query = query.where(MediaFile.file_size <= search_request.max_size)

    # Filter by analysis results
    if search_request.genres:
        genre_filters = []
        for genre in search_request.genres:
            genre_filters.append(
                MediaAnalysis.results["predictions"]["genres"].astext.ilike(
                    f"%{genre}%"
                )
            )
        query = query.where(or_(*genre_filters))

    if search_request.moods:
        mood_filters = []
        for mood in search_request.moods:
            mood_filters.append(
                MediaAnalysis.results["predictions"]["moods"].astext.ilike(f"%{mood}%")
            )
        query = query.where(or_(*mood_filters))

    if search_request.min_tempo:
        query = query.where(
            MediaAnalysis.results["features"]["rhythm"]["tempo"].astext.cast(float)
            >= search_request.min_tempo
        )
    if search_request.max_tempo:
        query = query.where(
            MediaAnalysis.results["features"]["rhythm"]["tempo"].astext.cast(float)
            <= search_request.max_tempo
        )

    # Count total results
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    # Apply sorting
    if search_request.sort_by == "name":
        query = query.order_by(MediaFile.file_name)
    elif search_request.sort_by == "size":
        query = query.order_by(MediaFile.file_size.desc())
    elif search_request.sort_by == "created":
        query = query.order_by(MediaFile.created_at.desc())
    elif search_request.sort_by == "modified":
        query = query.order_by(MediaFile.updated_at.desc())
    else:
        # Default: newest first
        query = query.order_by(MediaFile.created_at.desc())

    # Apply pagination
    offset = (search_request.page - 1) * search_request.size
    query = query.offset(offset).limit(search_request.size)

    # Execute query
    result = await session.execute(query)
    rows = result.all()

    # Build results
    results = []
    for media_file, analysis in rows:
        result_item = SearchResult(
            id=media_file.id,
            catalog_id=media_file.catalog_id,
            file_name=media_file.file_name,
            file_size=media_file.file_size,
            media_type=media_file.media_type,
            mime_type=media_file.mime_type,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at,
            metadata=media_file.metadata,
        )

        if analysis:
            result_item.analysis = {
                "status": analysis.status,
                "genres": analysis.results.get("predictions", {}).get("genres", []),
                "moods": analysis.results.get("predictions", {}).get("moods", {}),
                "attributes": analysis.results.get("predictions", {}).get(
                    "attributes", {}
                ),
                "quality_score": analysis.results.get("quality_score", 0),
            }

        results.append(result_item)

    # Calculate total pages
    pages = (total + search_request.size - 1) // search_request.size if total > 0 else 0

    logger.info("✅ Search completed: %d results found", total)

    return {
        "results": results,
        "total": total,
        "page": search_request.page,
        "size": search_request.size,
        "pages": pages,
    }


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, list[str]]:
    """Get search suggestions based on partial query."""
    logger.info("💡 Getting suggestions for: %s", q)

    from shared.models import Catalog, MediaFile

    suggestions = set()

    # Search in file names
    query = (
        select(MediaFile.file_name)
        .join(Catalog)
        .where(
            Catalog.user_id == current_user.username,
            MediaFile.file_name.ilike(f"%{q}%"),
        )
        .limit(limit)
    )

    result = await session.execute(query)
    for (name,) in result:
        suggestions.add(name)

    # TODO: Search in tags, genres, etc.

    return {"suggestions": sorted(list(suggestions))[:limit]}
