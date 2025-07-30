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
    import hashlib
    import xxhash

    # Compute hashes
    sha256_hash = hashlib.sha256(content).hexdigest()
    xxh128_hash = xxhash.xxh128(content).hexdigest()

    media_file = MediaFile(
        catalog_id=catalog_id,
        file_path=str(file_path),
        file_name=file.filename,  # validated above
        filename=file.filename,  # For database compatibility
        original_path=str(file_path),
        file_size=file.size or 0,
        size=file.size or 0,  # For database compatibility
        media_type=media_type,
        mime_type=file.content_type,
        sha256_hash=sha256_hash,
        xxh128_hash=xxh128_hash,
        extension=file_ext,
        file_metadata={
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


@router.post("/", response_model=MediaFileResponse, status_code=status.HTTP_201_CREATED)
async def create_media_file(
    media_data: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Create a media file record (for testing)."""
    from shared.models import MediaFile
    import hashlib

    # Create media file record
    file_name = media_data.get("file_name", media_data.get("filename", "test.mp3"))
    media_file = MediaFile(
        file_name=file_name,
        filename=file_name,  # For database compatibility
        file_path=media_data.get("file_path", media_data.get("path", "/data/test.mp3")),
        original_path=media_data.get(
            "file_path", media_data.get("path", "/data/test.mp3")
        ),
        file_size=media_data.get("file_size", media_data.get("size", 0)),
        size=media_data.get(
            "file_size", media_data.get("size", 0)
        ),  # For database compatibility
        media_type=media_data.get("media_type", "audio"),
        sha256_hash=media_data.get(
            "hash_sha256",
            media_data.get("sha256_hash", hashlib.sha256(b"test").hexdigest()),
        ),
        xxh128_hash=media_data.get(
            "hash_xxh128", media_data.get("xxh128_hash", "test123")
        ),
        extension=Path(file_name).suffix,
        mime_type=media_data.get("mime_type", "audio/mpeg"),
    )

    session.add(media_file)
    await session.commit()
    await session.refresh(media_file)

    return MediaFileResponse(
        id=media_file.id,
        catalog_id=UUID("00000000-0000-0000-0000-000000000000"),  # Default catalog
        file_path=media_file.file_path,
        file_name=media_file.file_name,
        file_size=media_file.file_size,
        media_type=media_file.media_type,
        mime_type=media_file.mime_type,
        hash_sha256=media_file.sha256_hash,
        hash_xxh128=media_file.xxh128_hash,
        metadata={},
        status="active",
        created_at=media_file.created_at,
        updated_at=media_file.updated_at,
    )


@router.patch("/{media_id}", response_model=MediaFileResponse)
async def update_media_file(
    media_id: UUID,
    update_data: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Update media file details."""
    from shared.models import MediaFile

    media_file = await session.get(MediaFile, media_id)

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    # Update fields
    if "file_size" in update_data:
        media_file.file_size = update_data["file_size"]
        media_file.size = update_data["file_size"]  # For database compatibility
    if "size" in update_data:
        media_file.file_size = update_data["size"]
        media_file.size = update_data["size"]  # For database compatibility
    if "file_name" in update_data:
        media_file.file_name = update_data["file_name"]
        media_file.filename = update_data["file_name"]  # For database compatibility
    if "media_type" in update_data:
        media_file.media_type = update_data["media_type"]

    await session.commit()
    await session.refresh(media_file)

    # Invalidate cache
    await cache_delete(f"media:{media_id}")

    return MediaFileResponse(
        id=media_file.id,
        catalog_id=UUID("00000000-0000-0000-0000-000000000000"),  # Default catalog
        file_path=media_file.file_path,
        file_name=media_file.file_name,
        file_size=media_file.file_size,
        media_type=media_file.media_type,
        mime_type=media_file.mime_type,
        hash_sha256=media_file.sha256_hash,
        hash_xxh128=media_file.xxh128_hash,
        metadata={},
        status="active",
        created_at=media_file.created_at,
        updated_at=media_file.updated_at,
    )


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
