"""Catalog management endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..endpoints.auth import User, get_current_active_user
from ..schemas.catalog import (
    CatalogCreate,
    CatalogResponse,
    CatalogUpdate,
    MediaFileResponse,
)
from ..utils.cache import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter()


class PaginatedResponse(BaseModel):
    """Paginated response model."""

    items: list[Any]
    total: int
    page: int
    size: int
    pages: int


@router.get("/", response_model=PaginatedResponse)
async def list_catalogs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """List all catalogs with pagination."""
    logger.info("📚 Listing catalogs for user: %s", current_user.username)

    # Build query
    from shared.models import Catalog

    query = select(Catalog).where(Catalog.user_id == current_user.username)

    if search:
        query = query.where(
            Catalog.name.ilike(f"%{search}%") | Catalog.description.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    result = await session.execute(query)
    catalogs = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size if total > 0 else 0

    return {
        "items": [CatalogResponse.from_orm(c) for c in catalogs],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.post("/", response_model=CatalogResponse, status_code=status.HTTP_201_CREATED)
async def create_catalog(
    catalog_data: CatalogCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new catalog."""
    logger.info("➕ Creating catalog: %s", catalog_data.name)

    from shared.models import Catalog

    # Check if catalog with same name exists
    existing = await session.scalar(
        select(Catalog).where(
            Catalog.user_id == current_user.username,
            Catalog.name == catalog_data.name,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Catalog with this name already exists",
        )

    # Create catalog
    catalog = Catalog(
        user_id=current_user.username,
        name=catalog_data.name,
        description=catalog_data.description,
        settings=catalog_data.settings or {},
    )

    session.add(catalog)
    await session.commit()
    await session.refresh(catalog)

    logger.info("✅ Created catalog: %s (ID: %s)", catalog.name, catalog.id)

    return CatalogResponse.from_orm(catalog)


@router.get("/{catalog_id}", response_model=CatalogResponse)
async def get_catalog(
    catalog_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get catalog by ID."""
    # Try cache first
    cache_key = f"catalog:{catalog_id}"
    cached = await cache_get(cache_key)
    if cached:
        logger.info("💾 Cache hit for catalog: %s", catalog_id)
        return CatalogResponse(**cached)

    from shared.models import Catalog

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

    # Cache the result
    response = CatalogResponse.from_orm(catalog)
    await cache_set(cache_key, response.dict(), ttl=3600)

    return response


@router.put("/{catalog_id}", response_model=CatalogResponse)
async def update_catalog(
    catalog_id: UUID,
    catalog_data: CatalogUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update catalog."""
    logger.info("✏️ Updating catalog: %s", catalog_id)

    from shared.models import Catalog

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

    # Update fields
    for field, value in catalog_data.dict(exclude_unset=True).items():
        setattr(catalog, field, value)

    catalog.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(catalog)

    # Invalidate cache
    await cache_delete(f"catalog:{catalog_id}")

    logger.info("✅ Updated catalog: %s", catalog_id)

    return CatalogResponse.from_orm(catalog)


@router.delete("/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog(
    catalog_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete catalog."""
    logger.info("🗑️ Deleting catalog: %s", catalog_id)

    from shared.models import Catalog

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

    await session.delete(catalog)
    await session.commit()

    # Invalidate cache
    await cache_delete(f"catalog:{catalog_id}")

    logger.info("✅ Deleted catalog: %s", catalog_id)


@router.get("/{catalog_id}/media", response_model=PaginatedResponse)
async def list_catalog_media(
    catalog_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    media_type: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """List media files in catalog."""
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

    # Build query
    query = select(MediaFile).where(MediaFile.catalog_id == catalog_id)

    if media_type:
        query = query.where(MediaFile.media_type == media_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Paginate
    query = (
        query.offset((page - 1) * size)
        .limit(size)
        .order_by(MediaFile.created_at.desc())
    )
    result = await session.execute(query)
    media_files = result.scalars().all()

    # Calculate pages
    pages = (total + size - 1) // size if total > 0 else 0

    return {
        "items": [MediaFileResponse.from_orm(m) for m in media_files],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
