"""Unit tests for the Prospector class."""
# mypy: disable-error-code="name-defined"

import hashlib
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import xxhash
from freezegun import freeze_time

from ingestor.prospector import Prospector


class TestProspector:
    """Test cases for the Prospector class."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[Path]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_file(self, temp_dir: Path) -> Path:
        """Create a test file."""
        file_path = temp_dir / "test_file.txt"
        file_path.write_text("Hello, World!")
        return file_path

    @pytest.fixture
    def test_file_with_neighbors(self, temp_dir: Path) -> Path:
        """Create a test file with neighbor files."""
        # Main file
        main_file = temp_dir / "video.mp4"
        main_file.write_text("video content")

        # Neighbor files
        (temp_dir / "video.srt").write_text("subtitles")
        (temp_dir / "video.nfo").write_text("info")
        (temp_dir / "tracklist.txt").write_text("tracks")
        (temp_dir / "readme.txt").write_text("readme")
        (temp_dir / "vid001.jpg").write_text("thumbnail")  # Starts with same 3 chars

        # Non-neighbor files
        (temp_dir / "other.txt").write_text("other")
        (temp_dir / "ab.txt").write_text("too short stem match")

        return main_file

    def test_prospector_initialization_with_string(self) -> None:
        """Test Prospector can be initialized with string path."""
        prospector = Prospector("/test/path/file.txt")
        assert isinstance(prospector.path, Path)
        assert str(prospector.path) == "/test/path/file.txt"

    def test_prospector_initialization_with_path(self) -> None:
        """Test Prospector can be initialized with Path object."""
        path = Path("/test/path/file.txt")
        prospector = Prospector(path)
        assert prospector.path is path

    @pytest.mark.asyncio
    @freeze_time("2024-01-01 12:00:00")
    async def test_prospect_successful(self, test_file: Path) -> None:
        """Test successful file prospecting."""
        prospector = Prospector(test_file)
        result = await prospector.prospect()

        # Check basic fields
        assert result["file_path"] == str(test_file.absolute())
        assert result["event_type"] == "IN_CREATE"
        assert result["timestamp"] == "2024-01-01T12:00:00+00:00"

        # Check file stats
        assert result["size"] == 13  # "Hello, World!" is 13 bytes
        assert "modified_time" in result
        assert "accessed_time" in result
        assert "changed_time" in result

        # Check hashes
        assert len(result["sha256_hash"]) == 64  # SHA256 is 64 hex chars
        assert len(result["xxh128_hash"]) == 32  # xxh128 is 32 hex chars

        # Verify correct hash values
        expected_sha256 = hashlib.sha256(b"Hello, World!").hexdigest()
        expected_xxh128 = xxhash.xxh128(b"Hello, World!").hexdigest()
        assert result["sha256_hash"] == expected_sha256
        assert result["xxh128_hash"] == expected_xxh128

        # Check neighbors
        assert isinstance(result["neighbors"], list)

    @pytest.mark.asyncio
    async def test_prospect_missing_file(self, temp_dir: Path) -> None:
        """Test prospecting a non-existent file."""
        missing_file = temp_dir / "missing.txt"
        prospector = Prospector(missing_file)

        result = await prospector.prospect()

        # Should still return basic data
        assert result["file_path"] == str(missing_file.absolute())
        assert result["event_type"] == "IN_CREATE"
        assert "timestamp" in result

        # No stats data
        assert "size" not in result
        assert "modified_time" not in result

        # Empty hashes
        assert result["sha256_hash"] == ""
        assert result["xxh128_hash"] == ""

        # Empty neighbors
        assert result["neighbors"] == []

    @pytest.mark.asyncio
    async def test_prospect_permission_error(self, temp_dir: Path) -> None:
        """Test prospecting handles permission errors gracefully."""
        test_file = temp_dir / "restricted.txt"
        test_file.write_text("content")

        # Mock stat to raise error only for the test file
        original_stat = Path.stat

        def mock_stat(self: Path, *args: Any, **kwargs: Any) -> Any:
            # If this is our test file, raise permission error
            if self == test_file:
                raise OSError("Permission denied")
            # Otherwise, call the original stat method
            return original_stat(self, *args, **kwargs)

        with patch.object(Path, "stat", mock_stat):
            prospector = Prospector(test_file)
            result = await prospector.prospect()

            # Should still return basic data
            assert result["file_path"] == str(test_file.absolute())
            assert "timestamp" in result

            # No stats data
            assert "size" not in result

    def test_compute_hashes_successful(self, test_file: Path) -> None:
        """Test hash computation for a regular file."""
        prospector = Prospector(test_file)
        hashes = prospector._compute_hashes()

        # SHA256 of "Hello, World!"
        expected_sha256 = hashlib.sha256(b"Hello, World!").hexdigest()
        expected_xxh128 = xxhash.xxh128(b"Hello, World!").hexdigest()
        assert hashes["sha256"] == expected_sha256
        assert hashes["xxh128"] == expected_xxh128

    def test_compute_hashes_large_file(self, temp_dir: Path) -> None:
        """Test hash computation handles large files with chunking."""
        # Create a file larger than chunk size (64KB)
        large_file = temp_dir / "large.bin"
        large_data = b"x" * (100 * 1024)  # 100KB
        large_file.write_bytes(large_data)

        prospector = Prospector(large_file)
        hashes = prospector._compute_hashes()

        # Verify hashes
        expected_sha256 = hashlib.sha256(large_data).hexdigest()
        expected_xxh128 = xxhash.xxh128(large_data).hexdigest()
        assert hashes["sha256"] == expected_sha256
        assert hashes["xxh128"] == expected_xxh128

    def test_compute_hashes_read_error(self, temp_dir: Path) -> None:
        """Test hash computation handles read errors."""
        test_file = temp_dir / "error.txt"
        test_file.write_text("content")

        with patch.object(Path, "open", side_effect=OSError("Read error")):
            prospector = Prospector(test_file)
            hashes = prospector._compute_hashes()

            assert hashes["sha256"] == ""
            assert hashes["xxh128"] == ""

    def test_find_neighbors_with_matches(self, test_file_with_neighbors: Path) -> None:
        """Test finding neighbor files."""
        prospector = Prospector(test_file_with_neighbors)
        neighbors = prospector._find_neighbors()

        # Should find the related files
        neighbor_names = [Path(n).name for n in neighbors]
        assert "video.srt" in neighbor_names
        assert "video.nfo" in neighbor_names
        assert "tracklist.txt" in neighbor_names
        assert "readme.txt" in neighbor_names
        assert "vid001.jpg" in neighbor_names

        # Should not find unrelated files
        assert "other.txt" not in neighbor_names
        assert "ab.txt" not in neighbor_names  # Too short stem

    def test_find_neighbors_no_parent(self) -> None:
        """Test finding neighbors when parent directory doesn't exist."""
        prospector = Prospector("/non/existent/path/file.txt")
        neighbors = prospector._find_neighbors()

        assert neighbors == []

    def test_find_neighbors_limit(self, temp_dir: Path) -> None:
        """Test neighbor limit of 10 files."""
        # Create main file
        main_file = temp_dir / "main.txt"
        main_file.write_text("main")

        # Create 15 neighbor files
        for i in range(15):
            (temp_dir / f"main_{i}.txt").write_text(f"neighbor {i}")

        prospector = Prospector(main_file)
        neighbors = prospector._find_neighbors()

        # Should only return 10 neighbors
        assert len(neighbors) == 10

    def test_find_neighbors_directory_error(self, temp_dir: Path) -> None:
        """Test finding neighbors handles directory errors."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        with patch.object(Path, "iterdir", side_effect=OSError("Directory error")):
            prospector = Prospector(test_file)
            neighbors = prospector._find_neighbors()

            assert neighbors == []

    def test_find_neighbors_case_insensitive_special_names(self, temp_dir: Path) -> None:
        """Test finding neighbors matches special names case-insensitively."""
        # Create main file
        main_file = temp_dir / "video.mp4"
        main_file.write_text("video")

        # Create special named files with different cases
        (temp_dir / "TRACKLIST.txt").write_text("tracks")
        (temp_dir / "Tracks.txt").write_text("tracks")
        (temp_dir / "INFO.nfo").write_text("info")
        (temp_dir / "ReadMe.md").write_text("readme")

        prospector = Prospector(main_file)
        neighbors = prospector._find_neighbors()

        neighbor_names = [Path(n).name for n in neighbors]
        assert "TRACKLIST.txt" in neighbor_names
        assert "Tracks.txt" in neighbor_names
        assert "INFO.nfo" in neighbor_names
        assert "ReadMe.md" in neighbor_names

    def test_find_neighbors_excludes_directories(self, temp_dir: Path) -> None:
        """Test that directories are excluded from neighbors."""
        # Create main file
        main_file = temp_dir / "video.mp4"
        main_file.write_text("video")

        # Create a directory with matching name
        (temp_dir / "video_dir").mkdir()

        # Create a matching file
        (temp_dir / "video.srt").write_text("subtitles")

        prospector = Prospector(main_file)
        neighbors = prospector._find_neighbors()

        neighbor_names = [Path(n).name for n in neighbors]
        assert "video.srt" in neighbor_names
        assert "video_dir" not in neighbor_names

    @pytest.mark.asyncio
    async def test_prospect_with_string_path(self) -> None:
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
    async def test_prospect_symlink(self, temp_dir: Path) -> None:
        """Test prospector with symbolic links."""
        # Create real file
        real_file = temp_dir / "real.txt"
        real_file.write_text("real content")

        # Create symlink
        symlink = temp_dir / "link.txt"
        symlink.symlink_to(real_file)

        prospector = Prospector(symlink)
        result = await prospector.prospect()

        # Should process the symlink target
        assert "file_path" in result
        assert result["size"] == len("real content")
        assert result["sha256_hash"] != ""

    @pytest.mark.asyncio
    async def test_prospect_file_permissions_unix(self, test_file: Path) -> None:
        """Test prospector with a file that has read permission issues on Unix."""
        if not hasattr(os, "chmod"):
            pytest.skip("chmod not available on this platform")

        # Remove read permissions
        test_file.chmod(0o000)

        try:
            prospector = Prospector(test_file)
            result = await prospector.prospect()

            # Should handle gracefully - stats might work but read won't
            assert result["sha256_hash"] == ""
            assert result["xxh128_hash"] == ""
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_prospect_integration(self, test_file_with_neighbors: Path) -> None:
        """Test complete prospect workflow with neighbors."""
        prospector = Prospector(test_file_with_neighbors)
        result = await prospector.prospect()

        # Check all fields are present
        assert "file_path" in result
        assert "event_type" in result
        assert "timestamp" in result
        assert "size" in result
        assert "sha256_hash" in result
        assert "xxh128_hash" in result
        assert "neighbors" in result

        # Check neighbors were found
        assert len(result["neighbors"]) > 0
        neighbor_names = [Path(n).name for n in result["neighbors"]]
        assert "video.srt" in neighbor_names

        # Verify timestamp format is ISO with timezone
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert timestamp.tzinfo is not None
