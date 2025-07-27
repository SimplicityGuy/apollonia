"""Tests for the Prospector class."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import xxhash

# Skip on macOS as the ingestor module uses asyncinotify which is Linux-only
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="asyncinotify requires Linux")

if sys.platform != "darwin":
    from ingestor.prospector import Prospector


@pytest.mark.asyncio
async def test_prospector_basic() -> None:
    """Test basic prospector functionality."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tf:
        test_content = "test content"
        tf.write(test_content)
        temp_path = Path(tf.name)

    try:
        prospector = Prospector(temp_path)
        result = await prospector.prospect()

        # Check required fields
        assert "file_path" in result
        assert "sha256_hash" in result
        assert "xxh128_hash" in result
        assert "neighbors" in result
        assert "timestamp" in result
        assert "size" in result
        assert "event_type" in result

        # Verify hashes are correct
        expected_sha256 = hashlib.sha256(test_content.encode()).hexdigest()
        expected_xxh128 = xxhash.xxh128(test_content.encode()).hexdigest()
        assert result["sha256_hash"] == expected_sha256
        assert result["xxh128_hash"] == expected_xxh128

        # Verify other fields
        assert Path(result["file_path"]).is_absolute()
        assert result["size"] == len(test_content)
        assert result["event_type"] == "IN_CREATE"
        assert isinstance(result["neighbors"], list)

        # Verify timestamp format
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert timestamp.tzinfo is not None

    finally:
        # Cleanup
        temp_path.unlink()


@pytest.mark.asyncio
async def test_prospector_with_string_path() -> None:
    """Test prospector with string path instead of Path object."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write("string path test")
        temp_path = tf.name

    try:
        prospector = Prospector(temp_path)  # String path
        result = await prospector.prospect()

        assert "file_path" in result
        assert Path(result["file_path"]).is_absolute()

    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_prospector_large_file() -> None:
    """Test prospector with a larger file to verify chunked hashing."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
        # Write 1MB of data
        data = b"x" * (1024 * 1024)
        tf.write(data)
        temp_path = Path(tf.name)

    try:
        prospector = Prospector(temp_path)
        result = await prospector.prospect()

        # Verify hashes
        expected_sha256 = hashlib.sha256(data).hexdigest()
        expected_xxh128 = xxhash.xxh128(data).hexdigest()
        assert result["sha256_hash"] == expected_sha256
        assert result["xxh128_hash"] == expected_xxh128
        assert result["size"] == 1024 * 1024

    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_prospector_neighbors() -> None:
    """Test neighbor file discovery."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create main file and neighbors
        main_file = tmpdir_path / "test.mp3"
        main_file.write_text("main content")

        # Create neighbor files
        (tmpdir_path / "test.txt").write_text("text file")
        (tmpdir_path / "test.log").write_text("log file")
        (tmpdir_path / "tracklist.txt").write_text("tracklist")
        (tmpdir_path / "readme.txt").write_text("readme")
        (tmpdir_path / "unrelated.doc").write_text("unrelated")

        prospector = Prospector(main_file)
        result = await prospector.prospect()

        neighbors = result["neighbors"]
        neighbor_names = [Path(n).name for n in neighbors]

        # Check expected neighbors are found
        assert "test.txt" in neighbor_names
        assert "test.log" in neighbor_names
        assert "tracklist.txt" in neighbor_names
        assert "readme.txt" in neighbor_names

        # Verify unrelated file is not included
        assert "unrelated.doc" not in neighbor_names

        # Verify main file is not in its own neighbors
        assert "test.mp3" not in neighbor_names

        # Verify max 10 neighbors limit
        assert len(neighbors) <= 10


@pytest.mark.asyncio
async def test_prospector_missing_file() -> None:
    """Test prospector with a non-existent file."""
    prospector = Prospector("/non/existent/file.txt")
    result = await prospector.prospect()

    # Should still return basic structure
    assert "file_path" in result
    assert "sha256_hash" in result
    assert "xxh128_hash" in result

    # Hashes should be empty for missing file
    assert result["sha256_hash"] == ""
    assert result["xxh128_hash"] == ""

    # Should not have size or timestamps
    assert "size" not in result


@pytest.mark.asyncio
async def test_prospector_file_permissions() -> None:
    """Test prospector with a file that has read issues."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write("permission test")
        temp_path = Path(tf.name)

    try:
        # Make file unreadable (Unix-like systems)
        import os

        if hasattr(os, "chmod"):
            temp_path.chmod(0o000)

            prospector = Prospector(temp_path)
            result = await prospector.prospect()

            # Should handle gracefully
            assert result["sha256_hash"] == ""
            assert result["xxh128_hash"] == ""

            # Restore permissions for cleanup
            temp_path.chmod(0o644)

    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_prospector_symlink() -> None:
    """Test prospector with symbolic links."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create real file
        real_file = tmpdir_path / "real.txt"
        real_file.write_text("real content")

        # Create symlink
        symlink = tmpdir_path / "link.txt"
        symlink.symlink_to(real_file)

        prospector = Prospector(symlink)
        result = await prospector.prospect()

        # Should process the symlink target
        assert "file_path" in result
        assert result["size"] == len("real content")
        assert result["sha256_hash"] != ""
