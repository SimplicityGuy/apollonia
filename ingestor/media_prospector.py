"""Enhanced prospector for media files with additional metadata extraction."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .media_utils import MediaFileDetector, extract_basic_metadata, find_related_media_files
from .prospector import Prospector

logger = logging.getLogger(__name__)


class MediaProspector(Prospector):
    """Enhanced prospector for media files."""

    def __init__(self, path: Path | str) -> None:
        """Initialize the MediaProspector.

        Args:
            path: The file path to prospect.
        """
        super().__init__(path)
        self.detector = MediaFileDetector()

    async def prospect(self) -> dict[str, Any]:
        """Collect enhanced metadata for media files.

        Returns:
            Dictionary containing file metadata including media-specific information.
        """
        # Get base metadata from parent class
        data = await super().prospect()

        # Add media-specific metadata
        if self.detector.is_media_file(self.path):
            logger.info("🎵 Detected media file: %s", self.path)

            # Extract basic media metadata
            media_metadata = extract_basic_metadata(self.path)
            data["media_metadata"] = media_metadata

            # Find related media files
            related_files = find_related_media_files(self.path)
            data["related_media"] = related_files

            # Set appropriate routing key based on media type
            if self.detector.is_audio_file(self.path):
                data["routing_key"] = "media.audio.created"
                logger.info("🎵 Audio file detected: %s", self.path.name)
            elif self.detector.is_video_file(self.path):
                data["routing_key"] = "media.video.created"
                logger.info("🎬 Video file detected: %s", self.path.name)
            else:
                data["routing_key"] = "file.created"
        else:
            data["routing_key"] = "file.created"

        return data
