"""Test utilities for API testing."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from api.endpoints.auth import User


def create_test_user(
    username: str = "testuser",
    email: str = "test@example.com",
    full_name: str = "Test User",
    disabled: bool = False,
) -> User:
    """Create a test user."""
    return User(
        username=username,
        email=email,
        full_name=full_name,
        disabled=disabled,
    )


def create_mock_media_file(
    id: UUID | None = None,
    filename: str = "test.mp3",
    size: int = 1024000,
    media_type: str = "audio",
) -> dict[str, Any]:
    """Create a mock media file object."""
    file_id = id or uuid4()
    return {
        "id": file_id,
        "filename": filename,
        "original_path": f"/data/{filename}",
        "size": size,
        "media_type": media_type,
        "extension": f".{filename.split('.')[-1]}",
        "sha256_hash": "abc123def456",
        "xxh128_hash": "xyz789uvw456",
        "mime_type": f"{media_type}/mpeg",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def create_mock_catalog(
    id: UUID | None = None,
    user_id: str = "testuser",
    name: str = "Test Catalog",
) -> dict[str, Any]:
    """Create a mock catalog object."""
    catalog_id = id or uuid4()
    return {
        "id": catalog_id,
        "user_id": user_id,
        "name": name,
        "description": "Test catalog description",
        "media_count": 0,
        "settings": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
