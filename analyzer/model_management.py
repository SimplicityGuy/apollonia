"""Enhanced model management with caching and download capabilities."""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import orjson

if TYPE_CHECKING:
    from .cache import CacheManager

logger = logging.getLogger(__name__)

# Model registry with download URLs (mock URLs for now)
MODEL_REGISTRY = {
    "genre_classifier": {
        "url": "https://models.apollonia.ai/genre_classifier_v1.tar.gz",
        "version": "1.0.0",
        "size_mb": 125,
        "sha256": "mock_sha256_genre_classifier",
        "description": "Multi-genre audio classifier trained on 1M songs",
        "input_shape": [None, 128],
        "output_classes": 50,
    },
    "mood_classifier": {
        "url": "https://models.apollonia.ai/mood_classifier_v1.tar.gz",
        "version": "1.0.0",
        "size_mb": 98,
        "sha256": "mock_sha256_mood_classifier",
        "description": "Mood and emotion classifier for audio",
        "input_shape": [None, 128],
        "output_classes": 12,
    },
    "attribute_extractor": {
        "url": "https://models.apollonia.ai/attribute_extractor_v1.tar.gz",
        "version": "1.0.0",
        "size_mb": 156,
        "sha256": "mock_sha256_attribute_extractor",
        "description": "Musical attribute extractor (tempo, key, etc.)",
        "input_shape": [None, 128],
        "outputs": ["attributes", "vocal", "tonality"],
    },
    "instrument_detector": {
        "url": "https://models.apollonia.ai/instrument_detector_v1.tar.gz",
        "version": "1.0.0",
        "size_mb": 203,
        "sha256": "mock_sha256_instrument_detector",
        "description": "Instrument detection and classification",
        "input_shape": [None, 128],
        "output_classes": 100,
    },
    "scene_classifier": {
        "url": "https://models.apollonia.ai/scene_classifier_v1.tar.gz",
        "version": "1.0.0",
        "size_mb": 245,
        "sha256": "mock_sha256_scene_classifier",
        "description": "Video scene classification model",
        "input_shape": [224, 224, 3],
        "output_classes": 80,
    },
}


class ModelDownloader:
    """Handles model downloading and verification."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize model downloader.

        Args:
            cache_dir: Directory to store downloaded models
        """
        self.cache_dir = cache_dir
        self.download_dir = cache_dir / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_model(self, model_name: str, model_info: dict[str, Any]) -> Path:
        """Download a model if not already present.

        Args:
            model_name: Name of the model
            model_info: Model metadata from registry

        Returns:
            Path to the downloaded model directory
        """
        model_dir = self.cache_dir / model_name / model_info["version"]

        # Check if model already exists
        if model_dir.exists() and self._verify_model(model_dir, model_info):
            logger.info("✅ Model %s v%s already downloaded", model_name, model_info["version"])
            return Path(model_dir)

        # Download model
        logger.info(
            "📥 Downloading model %s v%s (%d MB)",
            model_name,
            model_info["version"],
            model_info["size_mb"],
        )

        # In production, this would actually download from the URL
        # For now, we'll create a mock model structure
        await self._mock_download_model(model_name, model_info, model_dir)

        return Path(model_dir)

    async def _mock_download_model(
        self, model_name: str, model_info: dict[str, Any], model_dir: Path
    ) -> None:
        """Mock model download for development.

        Args:
            model_name: Name of the model
            model_info: Model metadata
            model_dir: Directory to save the model
        """
        model_dir.mkdir(parents=True, exist_ok=True)

        # Create mock model files
        config_file = model_dir / "config.json"
        model_file = model_dir / "model.bin"

        # Write mock config
        config = {
            "name": model_name,
            "version": model_info["version"],
            "architecture": "mock_architecture",
            "input_shape": model_info.get("input_shape"),
            "output_classes": model_info.get("output_classes"),
            "created_at": time.time(),
        }

        async with aiofiles.open(config_file, "wb") as f:
            await f.write(orjson.dumps(config))

        # Create mock model file
        async with aiofiles.open(model_file, "wb") as f:
            # Write some dummy data
            await f.write(b"MOCK_MODEL_DATA_" + model_name.encode() * 100)

        logger.info("✅ Mock model %s downloaded to %s", model_name, model_dir)

    def _verify_model(self, model_dir: Path, model_info: dict[str, Any]) -> bool:  # noqa: ARG002
        """Verify model integrity.

        Args:
            model_dir: Model directory
            model_info: Expected model metadata

        Returns:
            True if model is valid
        """
        # Check if essential files exist
        config_file = model_dir / "config.json"
        model_file = model_dir / "model.bin"

        return config_file.exists() and model_file.exists()

    async def cleanup_old_versions(self, model_name: str, keep_versions: int = 2) -> None:
        """Clean up old model versions.

        Args:
            model_name: Name of the model
            keep_versions: Number of recent versions to keep
        """
        model_base_dir = self.cache_dir / model_name
        if not model_base_dir.exists():
            return

        # Get all versions sorted by modification time
        versions = sorted(
            [d for d in model_base_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        # Remove old versions
        for version_dir in versions[keep_versions:]:
            logger.info("🗑️ Removing old model version: %s", version_dir)
            shutil.rmtree(version_dir)


class EnhancedModelManager:
    """Enhanced model manager with downloading and caching capabilities."""

    def __init__(
        self,
        cache_dir: Path,
        cache_manager: CacheManager | None = None,
    ) -> None:
        """Initialize enhanced model manager.

        Args:
            cache_dir: Directory to cache models
            cache_manager: Optional cache manager for metadata
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_manager = cache_manager
        self.downloader = ModelDownloader(cache_dir)
        self.models: dict[str, Any] = {}
        self._load_metrics = {
            "models_loaded": 0,
            "total_load_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def initialize(self) -> None:
        """Initialize models and download if necessary."""
        logger.info("🤖 Enhanced model initialization started")

        # Load model registry from cache if available
        if self.cache_manager:
            cached_registry = await self.cache_manager.get_model_metadata("registry")
            if cached_registry:
                logger.info("📦 Using cached model registry")
                self._load_metrics["cache_hits"] += 1
            else:
                # Cache the registry
                await self.cache_manager.set_model_metadata("registry", MODEL_REGISTRY)
                self._load_metrics["cache_misses"] += 1

        # Initialize each model
        tasks = []
        for model_name, model_info in MODEL_REGISTRY.items():
            tasks.append(self._initialize_model(model_name, model_info))

        await asyncio.gather(*tasks)

        logger.info(
            "✅ Models initialized (loaded: %d, cache hits: %d, total time: %.2fs)",
            self._load_metrics["models_loaded"],
            self._load_metrics["cache_hits"],
            self._load_metrics["total_load_time"],
        )

    async def _initialize_model(self, model_name: str, model_info: dict[str, Any]) -> None:
        """Initialize a single model.

        Args:
            model_name: Name of the model
            model_info: Model metadata
        """
        start_time = time.time()

        try:
            # Check cache for model metadata
            if self.cache_manager:
                cached_meta = await self.cache_manager.get_model_metadata(model_name)
                if cached_meta and cached_meta.get("version") == model_info["version"]:
                    logger.debug("📦 Using cached metadata for %s", model_name)
                    self._load_metrics["cache_hits"] += 1

            # Download model if needed
            model_dir = await self.downloader.download_model(model_name, model_info)

            # Load model (mock for now)
            from .models import MockModel

            self.models[model_name] = MockModel(model_name)

            # Update metrics
            load_time = time.time() - start_time
            self._load_metrics["models_loaded"] += 1
            self._load_metrics["total_load_time"] += load_time

            logger.info("✅ Model %s loaded in %.2fs", model_name, load_time)

            # Cache model metadata
            if self.cache_manager:
                metadata = {
                    **model_info,
                    "loaded_at": time.time(),
                    "load_time": load_time,
                    "model_dir": str(model_dir),
                }
                await self.cache_manager.set_model_metadata(model_name, metadata)

        except Exception as e:
            logger.error("🚨 Failed to initialize model %s: %s", model_name, e)
            # Fall back to mock model
            from .models import MockModel

            self.models[model_name] = MockModel(model_name)

    def get_model(self, model_name: str) -> Any:
        """Get a loaded model by name.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The loaded model instance

        Raises:
            KeyError: If model not found
        """
        if model_name not in self.models:
            raise KeyError(f"Model '{model_name}' not found")
        return self.models[model_name]

    async def update_models(self) -> dict[str, Any]:
        """Check for and download model updates.

        Returns:
            Dictionary with update results
        """
        logger.info("🔄 Checking for model updates...")

        updates: dict[str, Any] = {
            "checked": len(MODEL_REGISTRY),
            "updated": 0,
            "failed": 0,
            "models": {},
        }

        for model_name, model_info in MODEL_REGISTRY.items():
            try:
                # In production, this would check for new versions
                # For now, just verify current models
                model_dir = self.cache_dir / model_name / str(model_info["version"])
                if not model_dir.exists():
                    await self.downloader.download_model(model_name, model_info)
                    updates["updated"] = updates["updated"] + 1
                    updates["models"][model_name] = "updated"
                else:
                    updates["models"][model_name] = "up-to-date"
            except Exception as e:
                logger.error("🚨 Failed to update model %s: %s", model_name, e)
                updates["failed"] = updates["failed"] + 1
                updates["models"][model_name] = f"failed: {e}"

        logger.info(
            "✅ Model update complete (updated: %d, failed: %d)",
            updates["updated"],
            updates["failed"],
        )

        return updates

    async def cleanup(self) -> None:
        """Clean up old model versions and temporary files."""
        logger.info("🧹 Cleaning up old model versions...")

        cleanup_tasks = []
        for model_name in MODEL_REGISTRY:
            cleanup_tasks.append(self.downloader.cleanup_old_versions(model_name, keep_versions=2))

        await asyncio.gather(*cleanup_tasks)

        # Clean up download directory
        download_dir = self.cache_dir / "downloads"
        if download_dir.exists():
            for file in download_dir.iterdir():
                if file.is_file() and file.stat().st_mtime < time.time() - 86400:
                    file.unlink()
                    logger.debug("🗑️ Removed old download: %s", file.name)

    def get_metrics(self) -> dict[str, Any]:
        """Get model manager metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "models_loaded": len(self.models),
            "load_metrics": self._load_metrics,
            "cache_size_mb": self._calculate_cache_size(),
            "model_versions": {name: info["version"] for name, info in MODEL_REGISTRY.items()},
        }

    def _calculate_cache_size(self) -> float:
        """Calculate total size of cached models in MB.

        Returns:
            Total size in megabytes
        """
        total_size = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        return round(total_size / (1024 * 1024), 2)
