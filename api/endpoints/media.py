"""Media file management endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session
from ..endpoints.auth import User, get_current_active_user
from ..schemas.media import MediaAnalysisResponse, MediaFileResponse
from ..utils.cache import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media_file(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get media file details."""
    # Try cache first
    cache_key = f"media:{media_id}"
    cached = await cache_get(cache_key)
    if cached:
        logger.info("💾 Cache hit for media: %s", media_id)
        return MediaFileResponse(**cached)

    from shared.models import Catalog, MediaFile

    # Get media file with catalog
    result = await session.execute(
        select(MediaFile)
        .join(Catalog)
        .where(MediaFile.id == media_id, Catalog.user_id == current_user.username)
    )
    media_file = result.scalar_one_or_none()

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    # Cache the result
    response = MediaFileResponse.from_orm(media_file)
    await cache_set(cache_key, response.dict(), ttl=3600)

    return response


@router.get("/{media_id}/analysis", response_model=MediaAnalysisResponse)
async def get_media_analysis(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get media file ML analysis results."""
    # Try cache first
    cache_key = f"media:analysis:{media_id}"
    cached = await cache_get(cache_key)
    if cached:
        logger.info("💾 Cache hit for analysis: %s", media_id)
        return MediaAnalysisResponse(**cached)

    from shared.models import Catalog, MediaAnalysis, MediaFile

    # Get media file with analysis
    result = await session.execute(
        select(MediaFile, MediaAnalysis)
        .join(MediaAnalysis, MediaFile.id == MediaAnalysis.media_file_id)
        .join(Catalog)
        .where(MediaFile.id == media_id, Catalog.user_id == current_user.username)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media analysis not found",
        )

    media_file, analysis = row

    # Build response
    response = MediaAnalysisResponse(
        id=analysis.id,
        media_file_id=media_file.id,
        status=analysis.status,
        results=analysis.results,
        error=analysis.error,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )

    # Cache the result
    await cache_set(cache_key, response.dict(), ttl=3600)

    return response


@router.post("/{catalog_id}/upload", response_model=MediaFileResponse)
async def upload_media_file(
    catalog_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Upload a media file to catalog."""
    logger.info(
        "📤 Uploading file: %s to catalog: %s", file.filename or "unknown", catalog_id
    )

    # Verify catalog access
    from shared.models import Catalog, MediaFile

    catalog = await session.get(Catalog, catalog_id)

    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog not found",
        )

    if catalog.user_id != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Validate file
    settings = get_settings()

    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size} bytes",
        )

    # Determine media type from extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )
    file_ext = Path(file.filename).suffix.lower()

    media_type_map = {
        ".mp3": "audio",
        ".wav": "audio",
        ".flac": "audio",
        ".m4a": "audio",
        ".ogg": "audio",
        ".mp4": "video",
        ".avi": "video",
        ".mkv": "video",
        ".mov": "video",
        ".webm": "video",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".gif": "image",
        ".webp": "image",
    }

    media_type = media_type_map.get(file_ext, "unknown")

    if media_type == "unknown":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file_ext}",
        )

    # Save file (in production, this would upload to S3 or similar)
    upload_dir = Path(settings.upload_dir) / str(catalog_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename  # file.filename is validated above

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error("❌ Failed to save file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file",
        ) from e

    # Create media file record
    media_file = MediaFile(
        catalog_id=catalog_id,
        file_path=str(file_path),
        file_name=file.filename,  # validated above
        file_size=file.size or 0,
        media_type=media_type,
        mime_type=file.content_type,
        metadata={
            "uploaded_by": current_user.username,
            "original_filename": file.filename,  # validated above
        },
    )

    session.add(media_file)
    await session.commit()
    await session.refresh(media_file)

    logger.info(
        "✅ Uploaded media file: %s (ID: %s)", file.filename or "unknown", media_file.id
    )

    # TODO: Trigger ML analysis via message queue

    return MediaFileResponse.from_orm(media_file)


@router.delete("/{media_id}", response_class=Response)
async def delete_media_file(
    media_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Delete media file."""
    logger.info("🗑️ Deleting media file: %s", media_id)

    from shared.models import Catalog, MediaFile

    # Get media file with catalog
    result = await session.execute(
        select(MediaFile)
        .join(Catalog)
        .where(MediaFile.id == media_id, Catalog.user_id == current_user.username)
    )
    media_file = result.scalar_one_or_none()

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    # Delete physical file
    try:
        file_path = Path(media_file.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning("⚠️ Failed to delete physical file: %s", e)

    # Delete database record
    await session.delete(media_file)
    await session.commit()

    # Invalidate cache
    await cache_delete(f"media:{media_id}")
    await cache_delete(f"media:analysis:{media_id}")

    logger.info("✅ Deleted media file: %s", media_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
