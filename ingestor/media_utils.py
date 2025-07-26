"""Media file detection and metadata extraction utilities."""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Audio file extensions
AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
    ".ape",
    ".opus",
    ".webm",
    ".alac",
    ".aiff",
    ".dsd",
    ".dsf",
}

# Video file extensions
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".3gp",
    ".f4v",
    ".rm",
    ".rmvb",
    ".vob",
    ".ts",
}

# Image file extensions (for album art, thumbnails)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"}

# Metadata file extensions
METADATA_EXTENSIONS = {".cue", ".m3u", ".m3u8", ".pls", ".nfo", ".sfv", ".md5", ".sha256"}


class MediaFileDetector:
    """Detect and classify media files."""

    @staticmethod
    def is_media_file(path: Path) -> bool:
        """Check if file is a media file (audio or video).

        Args:
            path: File path to check

        Returns:
            True if file is audio or video
        """
        ext = path.suffix.lower()
        return ext in AUDIO_EXTENSIONS or ext in VIDEO_EXTENSIONS

    @staticmethod
    def is_audio_file(path: Path) -> bool:
        """Check if file is an audio file.

        Args:
            path: File path to check

        Returns:
            True if file is audio
        """
        return path.suffix.lower() in AUDIO_EXTENSIONS

    @staticmethod
    def is_video_file(path: Path) -> bool:
        """Check if file is a video file.

        Args:
            path: File path to check

        Returns:
            True if file is video
        """
        return path.suffix.lower() in VIDEO_EXTENSIONS

    @staticmethod
    def is_image_file(path: Path) -> bool:
        """Check if file is an image file.

        Args:
            path: File path to check

        Returns:
            True if file is image
        """
        return path.suffix.lower() in IMAGE_EXTENSIONS

    @staticmethod
    def is_metadata_file(path: Path) -> bool:
        """Check if file is a metadata file.

        Args:
            path: File path to check

        Returns:
            True if file is metadata
        """
        return path.suffix.lower() in METADATA_EXTENSIONS

    @staticmethod
    def get_media_type(path: Path) -> str:
        """Get the media type of a file.

        Args:
            path: File path to check

        Returns:
            Media type string: 'audio', 'video', 'image', 'metadata', or 'unknown'
        """
        ext = path.suffix.lower()

        if ext in AUDIO_EXTENSIONS:
            return "audio"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        elif ext in IMAGE_EXTENSIONS:
            return "image"
        elif ext in METADATA_EXTENSIONS:
            return "metadata"
        else:
            return "unknown"

    @staticmethod
    def get_mime_type(path: Path) -> str | None:
        """Get MIME type for a file.

        Args:
            path: File path

        Returns:
            MIME type string or None
        """
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type


def extract_basic_metadata(path: Path) -> dict[str, Any]:
    """Extract basic media metadata without external dependencies.

    Args:
        path: Media file path

    Returns:
        Dictionary with basic metadata
    """
    detector = MediaFileDetector()

    metadata: dict[str, Any] = {
        "media_type": detector.get_media_type(path),
        "mime_type": detector.get_mime_type(path),
        "extension": path.suffix.lower(),
        "filename": path.name,
        "stem": path.stem,
    }

    # Add directory structure info
    parts = path.parts
    if len(parts) > 2:
        # Try to infer artist/album from directory structure
        # Common patterns: /Artist/Album/Track.mp3 or /Music/Artist/Album/Track.mp3
        metadata["parent_dir"] = parts[-2] if len(parts) > 1 else None
        metadata["grandparent_dir"] = parts[-3] if len(parts) > 2 else None

    return metadata


def find_related_media_files(path: Path) -> dict[str, list[str]]:
    """Find related media files in the same directory.

    Args:
        path: Reference file path

    Returns:
        Dictionary categorizing related files
    """
    if not path.parent.exists():
        return {}

    related: dict[str, list[str]] = {
        "audio": [],
        "video": [],
        "images": [],
        "metadata": [],
        "subtitles": [],
    }

    detector = MediaFileDetector()
    stem = path.stem.lower()

    try:
        for file in path.parent.iterdir():
            if file == path or not file.is_file():
                continue

            file_stem = file.stem.lower()

            # Check for related files (same stem or similar)
            if (
                file_stem == stem
                or stem in file_stem
                or (len(stem) > 5 and file_stem.startswith(stem[:5]))
            ):
                media_type = detector.get_media_type(file)

                if media_type == "audio":
                    related["audio"].append(str(file))
                elif media_type == "video":
                    related["video"].append(str(file))
                elif media_type == "image":
                    related["images"].append(str(file))
                elif media_type == "metadata":
                    related["metadata"].append(str(file))
                elif file.suffix.lower() in {".srt", ".sub", ".ass", ".vtt"}:
                    related["subtitles"].append(str(file))

    except OSError:
        logger.exception("🚨 Failed to find related files for: %s", path)

    # Limit results
    for category in related:
        related[category] = related[category][:5]

    return related
