"""File prospecting functionality for extracting metadata."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import xxhash

logger = logging.getLogger(__name__)


class Prospector:
    """
    Prospector class provides a way to get some basic information about a file and
    related files. Related files can be seen as external metadata about the original
    file.

    Methods:
        prospect(): Collect all the information of the file specified by the path that
        is used elsewhere in apollonia.
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize the Prospector.

        Args:
            path: The file path to prospect.
        """
        self.path = Path(path) if isinstance(path, str) else path

    async def prospect(self) -> dict[str, Any]:
        """
        Collect all the information of the file specified by the path that is used
        elsewhere in apollonia.

        Returns:
            dict[str, Any]: Dictionary of the data collected.
        """
        """Collect file metadata.

        Returns:
            Dictionary containing file metadata including hashes, timestamps, and related files.
        """
        logger.debug("Prospecting file: %s", self.path)

        # Get file stats
        try:
            stats = self.path.stat()
        except OSError:
            logger.exception("Failed to stat file: %s", self.path)
            stats = None

        data: dict[str, Any] = {
            "file_path": str(self.path.absolute()),
            "event_type": "IN_CREATE",  # For compatibility
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Add file stats if available
        if stats:
            data.update(
                {
                    "size": stats.st_size,
                    "modified_time": datetime.fromtimestamp(stats.st_mtime, tz=UTC).isoformat(),
                    "accessed_time": datetime.fromtimestamp(stats.st_atime, tz=UTC).isoformat(),
                    "changed_time": datetime.fromtimestamp(stats.st_ctime, tz=UTC).isoformat(),
                }
            )

        # Add hashes
        hashes = self._compute_hashes()
        data["sha256_hash"] = hashes["sha256"]
        data["xxh128_hash"] = hashes["xxh128"]

        # Add neighbors
        data["neighbors"] = self._find_neighbors()

        return data

    def _compute_hashes(self) -> dict[str, str]:
        """Compute file hashes.

        Returns:
            Dictionary with SHA256 and xxh128 hashes.
        """
        hash_sha256 = sha256()
        hash_xxh128 = xxhash.xxh128()

        try:
            with self.path.open("rb") as f:
                while chunk := f.read(65536):  # 64KB chunks
                    hash_sha256.update(chunk)
                    hash_xxh128.update(chunk)
        except OSError:
            logger.exception("Failed to read file for hashing: %s", self.path)
            return {"sha256": "", "xxh128": ""}

        return {
            "sha256": hash_sha256.hexdigest(),
            "xxh128": hash_xxh128.hexdigest(),
        }

    def _find_neighbors(self) -> list[str]:
        """Find related files with similar naming.

        Returns:
            List of related file paths.
        """
        neighbors: list[str] = []

        if not self.path.parent.exists():
            return neighbors

        # Look for files with the same stem but different extensions
        stem = self.path.stem
        try:
            for file in self.path.parent.iterdir():
                if file.is_file() and file != self.path:
                    # Same stem, different extension
                    if (
                        file.stem == stem
                        or file.stem.lower() in ["tracklist", "tracks", "info", "readme"]
                        or len(stem) > 3
                        and file.stem.startswith(stem[:3])
                    ):
                        neighbors.append(str(file.absolute()))
        except OSError:
            logger.exception("Failed to search for neighbors of: %s", self.path)

        return neighbors[:10]  # Limit to 10 neighbors
