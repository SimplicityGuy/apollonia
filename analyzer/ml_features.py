"""
ML feature extraction for x86_64 platform.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Import essentia-tensorflow (x86_64 only)
try:
    import essentia.tensorflow as estf  # noqa: F401

    HAS_ESSENTIA_TF = True
    logger.info("Essentia-tensorflow loaded successfully")
except ImportError:
    HAS_ESSENTIA_TF = False
    logger.error("Failed to import essentia-tensorflow. Please ensure it's installed.")


class AudioFeatureExtractor:
    """Extract audio features using essentia-tensorflow and librosa."""

    def __init__(self) -> None:
        self.has_essentia_tf = HAS_ESSENTIA_TF
        if not self.has_essentia_tf:
            logger.warning("Essentia-tensorflow not available. Advanced features disabled.")

    def extract_features(self, audio_path: str) -> dict[str, Any]:
        """
        Extract audio features from the given file.

        Uses essentia-tensorflow (x86_64 only) and librosa for audio features.
        """
        features = {}

        if self.has_essentia_tf:
            # Use essentia-tensorflow for advanced features
            features.update(self._extract_essentia_features(audio_path))

        # Always use librosa for basic features
        features.update(self._extract_librosa_features(audio_path))

        return features

    def _extract_essentia_features(self, audio_path: str) -> dict[str, Any]:  # noqa: ARG002
        """Extract features using essentia-tensorflow (x86_64 only)."""
        if not self.has_essentia_tf:
            return {}

        # TODO: Implement essentia-tensorflow feature extraction
        # This would include music classification, mood detection, etc.
        return {
            "essentia_available": True,
            # Add actual feature extraction here
        }

    def _extract_librosa_features(self, audio_path: str) -> dict[str, Any]:
        """Extract features using librosa (all platforms)."""
        import librosa
        import numpy as np

        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)

            # Extract basic features
            features = {
                "duration": len(y) / sr,
                "sample_rate": sr,
                "tempo": float(librosa.beat.tempo(y=y, sr=sr)[0]),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
                "spectral_rolloff": float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))),
                "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(y))),
            }

            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(13):
                features[f"mfcc_{i}_mean"] = float(np.mean(mfccs[i]))
                features[f"mfcc_{i}_std"] = float(np.std(mfccs[i]))

            return features

        except Exception as e:
            logger.error(f"Error extracting librosa features: {e}")
            return {"librosa_error": str(e)}
