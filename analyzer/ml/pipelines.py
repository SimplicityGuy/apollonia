"""ML prediction pipelines for audio and video analysis."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from analyzer.models import ModelManager

    from .extractors import AudioFeatureExtractor, VideoFeatureExtractor

logger = logging.getLogger(__name__)


class MLPipeline(ABC):
    """Base class for ML prediction pipelines."""

    def __init__(self, model_manager: ModelManager) -> None:
        """Initialize the ML pipeline.

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager

    @abstractmethod
    async def predict(self, file_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Run ML predictions on a file.

        Args:
            file_path: Path to the media file
            metadata: Existing file metadata

        Returns:
            Dictionary containing prediction results
        """
        ...


class AudioPipeline(MLPipeline):
    """ML pipeline for audio file analysis."""

    def __init__(
        self,
        model_manager: ModelManager,
        feature_extractor: AudioFeatureExtractor,
    ) -> None:
        """Initialize the audio pipeline.

        Args:
            model_manager: Model manager instance
            feature_extractor: Audio feature extractor instance
        """
        super().__init__(model_manager)
        self.feature_extractor = feature_extractor

    async def predict(self, file_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        """Run audio ML predictions.

        Args:
            file_path: Path to the audio file
            metadata: Existing file metadata

        Returns:
            Dictionary containing prediction results
        """
        logger.info("🎵 Starting audio ML pipeline for: %s", file_path.name)

        # Extract features
        features = await self.feature_extractor.extract_features(file_path)

        # Run predictions in parallel
        tasks = [
            self._predict_genres(features),
            self._predict_moods(features),
            self._predict_attributes(features),
            self._predict_instruments(features),
            self._predict_vocal_characteristics(features),
        ]

        results = await asyncio.gather(*tasks)

        # Combine all results
        combined_results = {
            "features": features,
            "predictions": {
                "genres": results[0],
                "moods": results[1],
                "attributes": results[2],
                "instruments": results[3],
                "vocal": results[4],
            },
            "quality_score": self._calculate_quality_score(features),
            "processing_metadata": {
                "pipeline": "audio_v1",
                "feature_version": "1.0",
                "model_versions": {
                    "genre": "mock_1.0",
                    "mood": "mock_1.0",
                    "attributes": "mock_1.0",
                },
            },
        }

        logger.info("✅ Audio ML pipeline complete for: %s", file_path.name)
        return combined_results

    async def _predict_genres(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict music genres from features."""
        model = self.model_manager.get_model("genre_classifier")

        # In real implementation, we'd prepare features for the model
        # For now, use mock predictions influenced by features
        tempo = features["rhythm"]["tempo"]
        features["dynamics"]["rms_mean"]
        brightness = features["timbre"]["brightness"]

        # Mock genre prediction logic based on features
        predictions = await model.predict(None)
        genres = predictions["genres"]

        # Adjust predictions based on features
        if tempo > 140:  # Fast tempo
            for genre in genres:
                if genre["label"] in ["Electronic", "Dance", "Techno"]:
                    genre["confidence"] *= 1.2
                elif genre["label"] in ["Classical", "Jazz"]:
                    genre["confidence"] *= 0.8

        if brightness > 0.7:  # Bright sound
            for genre in genres:
                if genre["label"] in ["Pop", "Electronic"]:
                    genre["confidence"] *= 1.1

        # Normalize confidences
        total = sum(g["confidence"] for g in genres)
        for genre in genres:
            genre["confidence"] = round(genre["confidence"] / total, 3)

        # Sort by confidence and limit to top 5
        genres.sort(key=lambda x: float(x["confidence"]), reverse=True)
        return list(genres[:5])

    async def _predict_moods(self, features: dict[str, Any]) -> dict[str, float]:
        """Predict music moods from features."""
        model = self.model_manager.get_model("mood_classifier")

        # Get base predictions
        predictions = await model.predict(None)
        moods = predictions["moods"].copy()

        # Adjust based on features
        tempo = features["rhythm"]["tempo"]
        mode = features["harmonic"]["mode"]
        dynamics = features["dynamics"]["dynamic_range"]

        # Apply feature-based adjustments
        if tempo > 120:
            moods["party"] *= 1.3
            moods["relaxed"] *= 0.7
        else:
            moods["relaxed"] *= 1.2
            moods["party"] *= 0.8

        if mode == "minor":
            moods["sad"] *= 1.4
            moods["happy"] *= 0.7
        else:
            moods["happy"] *= 1.2
            moods["sad"] *= 0.8

        if dynamics > 20:
            moods["aggressive"] *= 1.3
            moods["acoustic"] *= 0.6

        # Normalize to 0-1 range
        for mood in moods:
            moods[mood] = round(min(max(moods[mood], 0), 1), 3)

        return dict(moods)

    async def _predict_attributes(self, features: dict[str, Any]) -> dict[str, float]:
        """Predict music attributes from features."""
        model = self.model_manager.get_model("attribute_extractor")

        # Get base predictions
        predictions = await model.predict(None)
        attributes = predictions["attributes"].copy()

        # Direct mapping from features
        attributes["energy"] = round(
            (features["dynamics"]["rms_mean"] + 20) / 15 * features["rhythm"]["beat_strength"],
            3,
        )
        attributes["danceability"] = round(
            min(features["rhythm"]["tempo"] / 180, 1) * features["rhythm"]["tempo_stability"],
            3,
        )
        attributes["acousticness"] = round(1 - features["timbre"]["brightness"], 3)
        attributes["instrumentalness"] = round(
            1 - features["timbre"]["warmth"] * 0.5,
            3,
        )
        attributes["valence"] = round(
            (features["timbre"]["clarity"] + features["harmonic"]["harmonic_complexity"]) / 2,
            3,
        )

        return dict(attributes)

    async def _predict_instruments(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict instruments present in the audio."""
        # Mock instrument detection based on spectral features
        instruments = []

        brightness = features["timbre"]["brightness"]
        warmth = features["timbre"]["warmth"]
        spectral_contrast = features["spectral"]["contrast"]

        # Logic for common instruments
        if brightness > 0.7 and warmth < 0.5:
            instruments.append({"name": "Synthesizer", "confidence": 0.85})
            instruments.append({"name": "Electronic Drums", "confidence": 0.78})

        if warmth > 0.6:
            instruments.append({"name": "Piano", "confidence": 0.72})
            instruments.append({"name": "Guitar", "confidence": 0.65})

        if max(spectral_contrast) > 30:
            instruments.append({"name": "Drums", "confidence": 0.82})
            instruments.append({"name": "Bass", "confidence": 0.76})

        # Sort by confidence
        instruments.sort(key=lambda x: float(str(x["confidence"])), reverse=True)
        return list(instruments[:5])

    async def _predict_vocal_characteristics(self, features: dict[str, Any]) -> dict[str, Any]:
        """Predict vocal characteristics."""
        model = self.model_manager.get_model("attribute_extractor")

        # Get base predictions
        predictions = await model.predict(None)
        vocal = predictions["vocal"].copy()

        # Adjust based on features
        instrumentalness = 1 - features["timbre"]["warmth"] * 0.5

        if instrumentalness > 0.7:
            vocal["instrumental"] = 0.9
            vocal["male"] = 0.05
            vocal["female"] = 0.05
        else:
            # Normalize non-instrumental predictions
            total = vocal["male"] + vocal["female"]
            vocal["male"] = round(vocal["male"] / total * (1 - vocal["instrumental"]), 3)
            vocal["female"] = round(vocal["female"] / total * (1 - vocal["instrumental"]), 3)

        return dict(vocal)

    def _calculate_quality_score(self, features: dict[str, Any]) -> float:
        """Calculate audio quality score from features."""
        # Mock quality scoring based on technical parameters
        score = 0.5  # Base score

        # Bitrate contribution
        bitrate = features["bitrate"]
        if bitrate >= 320000:
            score += 0.2
        elif bitrate >= 256000:
            score += 0.15
        elif bitrate >= 192000:
            score += 0.1

        # Dynamic range contribution
        dynamic_range = features["dynamics"]["dynamic_range"]
        if dynamic_range > 20:
            score += 0.15
        elif dynamic_range > 15:
            score += 0.1
        elif dynamic_range > 10:
            score += 0.05

        # Clarity contribution
        clarity = features["timbre"]["clarity"]
        score += clarity * 0.15

        return float(round(min(score, 1.0), 3))


class VideoPipeline(MLPipeline):
    """ML pipeline for video file analysis."""

    def __init__(
        self,
        model_manager: ModelManager,
        feature_extractor: VideoFeatureExtractor,
        audio_pipeline: AudioPipeline,
    ) -> None:
        """Initialize the video pipeline.

        Args:
            model_manager: Model manager instance
            feature_extractor: Video feature extractor instance
            audio_pipeline: Audio pipeline for audio track analysis
        """
        super().__init__(model_manager)
        self.feature_extractor = feature_extractor
        self.audio_pipeline = audio_pipeline

    async def predict(self, file_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Run video ML predictions.

        Args:
            file_path: Path to the video file
            metadata: Existing file metadata

        Returns:
            Dictionary containing prediction results
        """
        logger.info("🎬 Starting video ML pipeline for: %s", file_path.name)

        # Extract video features
        features = await self.feature_extractor.extract_features(file_path)

        results = {
            "features": features,
            "predictions": {},
        }

        # If video has audio, run audio pipeline
        if features["has_audio"] and "audio" in features:
            logger.info("🎵 Running audio analysis on video soundtrack...")
            audio_results = await self.audio_pipeline.predict(file_path, metadata)
            results["predictions"]["audio"] = audio_results["predictions"]

        # Run video-specific predictions
        tasks = [
            self._predict_video_genres(features),
            self._predict_video_moods(features),
            self._predict_scene_types(features),
            self._predict_video_quality(features),
        ]

        video_results = await asyncio.gather(*tasks)

        results["predictions"].update(
            {
                "video_genres": video_results[0],
                "video_moods": video_results[1],
                "scene_types": video_results[2],
                "quality_metrics": video_results[3],
            }
        )

        results["processing_metadata"] = {
            "pipeline": "video_v1",
            "feature_version": "1.0",
            "model_versions": {
                "video_classifier": "mock_1.0",
                "scene_detector": "mock_1.0",
            },
        }

        logger.info("✅ Video ML pipeline complete for: %s", file_path.name)
        return results

    async def _predict_video_genres(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict video genres/categories."""
        # Mock video genre prediction based on visual features
        genres = []

        motion = features["visual"]["motion_intensity"]
        scene_changes = features["visual"]["scene_changes"]
        face_count = features["content"]["face_count"]

        if motion > 0.7 and scene_changes > 50:
            genres.append({"label": "Action", "confidence": 0.85})
            genres.append({"label": "Sports", "confidence": 0.72})

        if face_count > 2:
            genres.append({"label": "Drama", "confidence": 0.68})
            genres.append({"label": "Documentary", "confidence": 0.55})

        if features["visual"]["avg_brightness"] < 0.4:
            genres.append({"label": "Thriller", "confidence": 0.62})
            genres.append({"label": "Horror", "confidence": 0.48})

        if not genres:
            genres.append({"label": "General", "confidence": 0.8})

        # Sort by confidence
        genres.sort(key=lambda x: float(str(x["confidence"])), reverse=True)
        return list(genres[:5])

    async def _predict_video_moods(self, features: dict[str, Any]) -> dict[str, float]:
        """Predict video moods from visual features."""
        brightness = features["visual"]["avg_brightness"]
        saturation = features["visual"]["avg_saturation"]
        motion = features["visual"]["motion_intensity"]

        moods = {
            "energetic": round(motion * 0.8 + saturation * 0.2, 3),
            "calm": round((1 - motion) * 0.7 + brightness * 0.3, 3),
            "dark": round((1 - brightness) * 0.9, 3),
            "vibrant": round(saturation * 0.85, 3),
            "dramatic": round(features["visual"]["avg_contrast"] * 0.9, 3),
            "peaceful": round((1 - motion) * (brightness * 0.6), 3),
        }

        return moods

    async def _predict_scene_types(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict types of scenes in the video."""
        scene_types = []

        # Mock scene detection based on features
        if features["content"]["face_count"] > 0:
            scene_types.append({"type": "People", "confidence": 0.9})

        if features["visual"]["dominant_colors"][0]["rgb"][1] > 150:  # Green dominant
            scene_types.append({"type": "Nature", "confidence": 0.75})

        if features["visual"]["avg_brightness"] > 0.7:
            scene_types.append({"type": "Outdoor", "confidence": 0.68})
        else:
            scene_types.append({"type": "Indoor", "confidence": 0.72})

        if features["content"]["text_presence"] > 0.2:
            scene_types.append({"type": "Text/Graphics", "confidence": 0.85})

        return scene_types

    async def _predict_video_quality(self, features: dict[str, Any]) -> dict[str, Any]:
        """Assess video quality metrics."""
        width = features["width"]
        height = features["height"]
        fps = features["fps"]
        bitrate = features["bitrate"]

        # Resolution score
        resolution_score = 0.5
        if width >= 3840:  # 4K
            resolution_score = 1.0
        elif width >= 1920:  # 1080p
            resolution_score = 0.85
        elif width >= 1280:  # 720p
            resolution_score = 0.7
        elif width >= 640:  # 480p
            resolution_score = 0.5

        # FPS score
        fps_score = min(fps / 60, 1.0)

        # Bitrate score (normalized to resolution)
        pixels_per_second = width * height * fps
        bits_per_pixel = bitrate / pixels_per_second
        bitrate_score = min(bits_per_pixel / 0.15, 1.0)  # 0.15 is good quality

        # Overall quality
        overall_quality = resolution_score * 0.4 + fps_score * 0.2 + bitrate_score * 0.4

        return {
            "resolution_score": round(resolution_score, 3),
            "fps_score": round(fps_score, 3),
            "bitrate_score": round(bitrate_score, 3),
            "overall_quality": round(overall_quality, 3),
            "resolution_label": self._get_resolution_label(width, height),
        }

    def _get_resolution_label(self, width: int, height: int) -> str:
        """Get human-readable resolution label."""
        if width >= 3840:
            return "4K"
        elif width >= 1920:
            return "1080p"
        elif width >= 1280:
            return "720p"
        elif width >= 640:
            return "480p"
        else:
            return f"{width}x{height}"
