"""Sample file fixtures for testing."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_directory: Path) -> Path:
    """Create a sample text file."""
    file_path = temp_directory / "sample.txt"
    file_path.write_text("This is a sample text file for testing.")
    return file_path


@pytest.fixture
def sample_binary_file(temp_directory: Path) -> Path:
    """Create a sample binary file."""
    file_path = temp_directory / "sample.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03" * 256)  # 1KB of binary data
    return file_path


@pytest.fixture
def sample_files_with_neighbors(temp_directory: Path) -> dict[str, Path]:
    """Create a set of related files."""
    files = {
        "main": temp_directory / "track01.mp3",
        "text": temp_directory / "track01.txt",
        "log": temp_directory / "track01.log",
        "tracklist": temp_directory / "tracklist.txt",
        "readme": temp_directory / "readme.txt",
        "unrelated": temp_directory / "other.doc",
    }

    for name, path in files.items():
        path.write_text(f"Content of {name} file")

    return files


@pytest.fixture
def large_file(temp_directory: Path) -> Path:
    """Create a large file for performance testing."""
    file_path = temp_directory / "large.dat"
    # Write 10MB of data
    chunk = b"x" * (1024 * 1024)  # 1MB
    with file_path.open("wb") as f:
        for _ in range(10):
            f.write(chunk)
    return file_path
