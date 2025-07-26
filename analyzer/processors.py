"""Media processing modules for ML analysis."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

try:
    # Try to import real pipelines (requires TensorFlow)
    from .ml.real_pipelines import RealAudioPipeline, RealVideoPipeline

    USE_REAL_ML = True
except ImportError:
    # Fall back to mock pipelines
    from .ml.extractors import AudioFeatureExtractor, VideoFeatureExtractor
    from .ml.pipelines import AudioPipeline, VideoPipeline

    USE_REAL_ML = False

if TYPE_CHECKING:
    from pathlib import Path

    from .models import ModelManager

logger = logging.getLogger(__name__)

if USE_REAL_ML:
    logger.info("✅ Using real ML pipelines with TensorFlow")
else:
    logger.warning("⚠️ TensorFlow not available, using mock ML pipelines")


class AudioProcessor:
    """Process audio files with ML models."""

    def __init__(self, model_manager: ModelManager) -> None:
        """Initialize audio processor.

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        if USE_REAL_ML:
            self.pipeline = RealAudioPipeline()
        else:
            self.feature_extractor = AudioFeatureExtractor()
            self.pipeline = AudioPipeline(model_manager, self.feature_extractor)

    async def process(self, file_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process an audio file with ML models.

        Args:
            file_path: Path to the audio file
            metadata: Existing file metadata

        Returns:
            Dictionary containing ML analysis results
        """
        logger.info("🎵 Processing audio file: %s", file_path.name)

        results: dict[str, Any] = {
            "status": "processed",
            "processor": "audio",
            "file_size": metadata.get("size", 0),
        }

        try:
            # Run the ML pipeline
            ml_results = await self.pipeline.predict(file_path, metadata)

            # Extract key results
            predictions = ml_results["predictions"]
            features = ml_results["features"]

            results.update(
                {
                    "genres": predictions["genres"],
                    "moods": predictions["moods"],
                    "attributes": predictions["attributes"],
                    "instruments": predictions["instruments"],
                    "vocal": predictions["vocal"],
                    "quality_score": ml_results["quality_score"],
                    "technical_info": {
                        "duration": features["duration"],
                        "sample_rate": features["sample_rate"],
                        "channels": features["channels"],
                        "bitrate": features["bitrate"],
                        "format": features["format"],
                    },
                    "audio_features": {
                        "tempo": features["rhythm"]["tempo"],
                        "key": features["harmonic"]["key"],
                        "mode": features["harmonic"]["mode"],
                        "loudness": features["dynamics"]["loudness"],
                        "dynamic_range": features["dynamics"]["dynamic_range"],
                    },
                    "processing_metadata": ml_results["processing_metadata"],
                }
            )

            logger.info("✅ Audio processing complete for: %s", file_path.name)

        except Exception:
            logger.exception("🚨 Error processing audio file: %s", file_path)
            results["status"] = "error"
            results["error"] = "Processing failed"

        return results


class VideoProcessor:
    """Process video files with ML models."""

    def __init__(self, model_manager: ModelManager) -> None:
        """Initialize video processor.

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        if USE_REAL_ML:
            self.pipeline = RealVideoPipeline()
        else:
            self.feature_extractor = VideoFeatureExtractor()
            audio_feature_extractor = AudioFeatureExtractor()
            audio_pipeline = AudioPipeline(model_manager, audio_feature_extractor)
            self.pipeline = VideoPipeline(model_manager, self.feature_extractor, audio_pipeline)

    async def process(self, file_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process a video file with ML models.

        Args:
            file_path: Path to the video file
            metadata: Existing file metadata

        Returns:
            Dictionary containing ML analysis results
        """
        logger.info("🎬 Processing video file: %s", file_path.name)

        results: dict[str, Any] = {
            "status": "processed",
            "processor": "video",
            "file_size": metadata.get("size", 0),
        }

        try:
            # Run the ML pipeline
            ml_results = await self.pipeline.predict(file_path, metadata)

            # Extract key results
            predictions = ml_results["predictions"]
            features = ml_results["features"]

            # Build results
            results["video_info"] = {
                "duration": features["duration"],
                "width": features["width"],
                "height": features["height"],
                "fps": features["fps"],
                "codec": features["codec"],
                "bitrate": features["bitrate"],
                "format": features["format"],
                "has_audio": features["has_audio"],
            }

            results["visual_analysis"] = {
                "scene_changes": features["visual"]["scene_changes"],
                "dominant_colors": features["visual"]["dominant_colors"],
                "motion_intensity": features["visual"]["motion_intensity"],
                "avg_brightness": features["visual"]["avg_brightness"],
                "avg_saturation": features["visual"]["avg_saturation"],
                "avg_contrast": features["visual"]["avg_contrast"],
            }

            results["content_analysis"] = features["content"]

            results["predictions"] = {
                "video_genres": predictions["video_genres"],
                "video_moods": predictions["video_moods"],
                "scene_types": predictions["scene_types"],
                "quality_metrics": predictions["quality_metrics"],
            }

            # Include audio analysis if present
            if features["has_audio"] and "audio" in predictions:
                results["audio_analysis"] = predictions["audio"]

            results["processing_metadata"] = ml_results["processing_metadata"]

            logger.info("✅ Video processing complete for: %s", file_path.name)

        except Exception:
            logger.exception("🚨 Error processing video file: %s", file_path)
            results["status"] = "error"
            results["error"] = "Processing failed"

        return results


# Real implementation would include:
"""
import librosa
import numpy as np
from moviepy.editor import VideoFileClip

class RealAudioProcessor:
    async def load_audio(self, file_path: Path) -> tuple[np.ndarray, int]:
        # Load audio file
        audio, sr = librosa.load(str(file_path), sr=16000)
        return audio, sr

    async def extract_features(self, audio: np.ndarray, sr: int) -> dict:
        # Extract various audio features
        features = {
            "mfcc": librosa.feature.mfcc(y=audio, sr=sr),
            "spectral_centroid": librosa.feature.spectral_centroid(y=audio, sr=sr),
            "tempo": librosa.beat.tempo(y=audio, sr=sr),
            # ... more features
        }
        return features

class RealVideoProcessor:
    async def extract_audio_from_video(self, video_path: Path) -> Path:
        # Extract audio track
        video = VideoFileClip(str(video_path))
        audio = video.audio

        audio_path = video_path.with_suffix('.wav')
        audio.write_audiofile(str(audio_path))

        return audio_path
"""
