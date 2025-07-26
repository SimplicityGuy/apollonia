"""Apollonia Ingestor - File monitoring service."""

from .ingestor import Ingestor
from .media_ingestor import MediaIngestor
from .media_prospector import MediaProspector
from .media_utils import MediaFileDetector

__version__ = "0.1.0"

__all__ = ["Ingestor", "MediaIngestor", "MediaProspector", "MediaFileDetector"]
