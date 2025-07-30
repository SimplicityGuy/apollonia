"""Performance benchmarks for hashing operations."""

import hashlib
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import xxhash


def generate_test_file(size_mb: int) -> Path:
    """Generate a test file of specified size in MB."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    content = b"x" * (1024 * 1024 * size_mb)
    temp_file.write(content)
    temp_file.close()
    return Path(temp_file.name)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_xxh128(file_path: Path) -> str:
    """Compute xxHash128 hash of a file."""
    xxh128_hash = xxhash.xxh128()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            xxh128_hash.update(chunk)
    return xxh128_hash.hexdigest()


@pytest.fixture(scope="session")
def small_test_file() -> Generator[Path, None, None]:
    """Create a 1MB test file."""
    file_path = generate_test_file(1)
    yield file_path
    file_path.unlink()


@pytest.fixture(scope="session")
def medium_test_file() -> Generator[Path, None, None]:
    """Create a 10MB test file."""
    file_path = generate_test_file(10)
    yield file_path
    file_path.unlink()


@pytest.fixture(scope="session")
def large_test_file() -> Generator[Path, None, None]:
    """Create a 100MB test file."""
    file_path = generate_test_file(100)
    yield file_path
    file_path.unlink()


class TestHashPerformance:
    """Benchmark tests for hash performance."""

    def test_sha256_small_file(self, benchmark: Any, small_test_file: Path) -> None:
        """Benchmark SHA256 hashing of a small file."""
        result = benchmark(compute_sha256, small_test_file)
        assert len(result) == 64  # SHA256 hex digest length

    def test_xxh128_small_file(self, benchmark: Any, small_test_file: Path) -> None:
        """Benchmark xxHash128 hashing of a small file."""
        result = benchmark(compute_xxh128, small_test_file)
        assert len(result) == 32  # xxHash128 hex digest length

    def test_sha256_medium_file(self, benchmark: Any, medium_test_file: Path) -> None:
        """Benchmark SHA256 hashing of a medium file."""
        result = benchmark(compute_sha256, medium_test_file)
        assert len(result) == 64

    def test_xxh128_medium_file(self, benchmark: Any, medium_test_file: Path) -> None:
        """Benchmark xxHash128 hashing of a medium file."""
        result = benchmark(compute_xxh128, medium_test_file)
        assert len(result) == 32

    @pytest.mark.slow
    def test_sha256_large_file(self, benchmark: Any, large_test_file: Path) -> None:
        """Benchmark SHA256 hashing of a large file."""
        result = benchmark(compute_sha256, large_test_file)
        assert len(result) == 64

    @pytest.mark.slow
    def test_xxh128_large_file(self, benchmark: Any, large_test_file: Path) -> None:
        """Benchmark xxHash128 hashing of a large file."""
        result = benchmark(compute_xxh128, large_test_file)
        assert len(result) == 32
