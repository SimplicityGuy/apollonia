"""ML analysis components for Apollonia analyzer."""

from .extractors import AudioFeatureExtractor, VideoFeatureExtractor
from .pipelines import AudioPipeline, MLPipeline, VideoPipeline

__all__ = [
    "AudioFeatureExtractor",
    "AudioPipeline",
    "MLPipeline",
    "VideoFeatureExtractor",
    "VideoPipeline",
]

# Try to import real ML components if available
try:
    from .real_models import (  # noqa: F401
        RealAudioFeatureExtractor,
        TensorFlowMusicModels,
    )
    from .real_models import VideoFeatureExtractor as RealVideoFeatureExtractor  # noqa: F401
    from .real_pipelines import RealAudioPipeline, RealVideoPipeline  # noqa: F401

    __all__.extend(
        [
            "RealAudioFeatureExtractor",
            "RealAudioPipeline",
            "RealVideoFeatureExtractor",
            "RealVideoPipeline",
            "TensorFlowMusicModels",
        ]
    )
except ImportError:
    pass  # Real ML components not available
