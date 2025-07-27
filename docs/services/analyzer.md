# ML Analyzer Service Documentation

The ML Analyzer service is responsible for extracting audio and video features using machine
learning models. It provides comprehensive analysis including spectral features, harmonic analysis,
and semantic content understanding.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [ML Models](#ml-models)
- [Performance](#performance)
- [Development](#development)

## Overview

The Analyzer service processes media files to extract:

- **Audio Features**: Spectral, temporal, and harmonic characteristics
- **Music Information Retrieval**: Tempo, key, time signature, genre classification
- **Content Analysis**: Mood, energy, acousticness, instrumentalness
- **Similarity Analysis**: Content-based similarity scoring
- **Quality Assessment**: Audio quality and technical parameters

### Key Capabilities

- **Multi-format Support**: MP3, WAV, FLAC, OGG, AAC, MP4, AVI, MOV
- **Real-time Processing**: Streaming analysis for live content
- **Batch Processing**: Efficient bulk analysis
- **GPU Acceleration**: CUDA support for faster processing
- **Model Versioning**: Support for multiple model versions

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                    ML Analyzer Service                      │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Message     │  │   Feature      │  │   Model        │ │
│  │   Consumer    │  │   Extractor    │  │   Manager      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Audio       │  │   Video        │  │   Result       │ │
│  │   Processor   │  │   Processor    │  │   Publisher    │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    ML Framework Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  TensorFlow   │  │    Essentia    │  │   Librosa      │ │
│  │    Models     │  │   Extractors   │  │   Features     │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```mermaid
graph LR
    A[AMQP Message] --> B[Message Consumer]
    B --> C[Media File Loader]
    C --> D[Format Detection]
    D --> E{Media Type}

    E -->|Audio| F[Audio Feature Extraction]
    E -->|Video| G[Video Feature Extraction]

    F --> H[Spectral Analysis]
    F --> I[Harmonic Analysis]
    F --> J[MIR Features]

    G --> K[Visual Features]
    G --> L[Audio Track Analysis]

    H --> M[Feature Aggregation]
    I --> M
    J --> M
    K --> M
    L --> M

    M --> N[Result Validation]
    N --> O[Database Storage]
    N --> P[AMQP Publishing]
```

## Features

### Audio Feature Extraction

#### Spectral Features

```python
# Low-level spectral characteristics
spectral_features = {
    "spectral_centroid": float,  # Brightness measure
    "spectral_rolloff": float,  # Frequency cutoff
    "spectral_bandwidth": float,  # Spectral spread
    "spectral_contrast": List[float],  # Spectral valley/peak
    "spectral_flatness": float,  # Spectral uniformity
    "zero_crossing_rate": float,  # Temporal characteristic
    "mfcc": List[float],  # Mel-frequency cepstral coefficients
    "chroma": List[float],  # Pitch class profiles
    "tonnetz": List[float],  # Tonal centroid features
}
```

#### Music Information Retrieval (MIR)

```python
# High-level music characteristics
mir_features = {
    "tempo": float,  # Beats per minute
    "key": str,  # Musical key (C, C#, D, etc.)
    "mode": str,  # Major or minor
    "time_signature": int,  # Time signature (4/4, 3/4, etc.)
    "onset_rate": float,  # Note onset frequency
    "beat_strength": float,  # Rhythmic clarity
    "key_strength": float,  # Tonal clarity
    "genre_probabilities": Dict[str, float],  # Genre classification scores
}
```

#### Perceptual Features

```python
# Human-perceived characteristics
perceptual_features = {
    "energy": float,  # Overall energy (0.0-1.0)
    "valence": float,  # Musical positivity (0.0-1.0)
    "danceability": float,  # Rhythmic suitability for dancing
    "acousticness": float,  # Acoustic vs electronic content
    "instrumentalness": float,  # Instrumental vs vocal content
    "liveness": float,  # Live performance indicators
    "speechiness": float,  # Speech-like content
    "loudness": float,  # Perceptual loudness (dB)
    "dynamic_range": float,  # Loudness variation
}
```

### Video Feature Extraction

#### Visual Features

```python
# Video content analysis
visual_features = {
    "scene_changes": List[float],  # Scene change timestamps
    "color_histogram": List[float],  # Color distribution
    "motion_vectors": List[float],  # Motion analysis
    "brightness": float,  # Average brightness
    "contrast": float,  # Visual contrast
    "saturation": float,  # Color saturation
    "faces_detected": int,  # Number of faces
    "text_regions": List[Dict],  # OCR text detection
}
```

#### Technical Analysis

```python
# Technical video characteristics
technical_features = {
    "resolution": Tuple[int, int],  # Width x Height
    "frame_rate": float,  # Frames per second
    "bit_rate": int,  # Video bit rate
    "codec": str,  # Video codec
    "duration": float,  # Duration in seconds
    "aspect_ratio": float,  # Width/Height ratio
    "has_audio": bool,  # Audio track present
    "audio_channels": int,  # Number of audio channels
    "quality_score": float,  # Overall quality assessment
}
```

## Configuration

### Environment Variables

```bash
# Service Configuration
ANALYZER_WORKERS=4                    # Number of worker processes
ANALYZER_BATCH_SIZE=10               # Files per batch
ANALYZER_MAX_MEMORY=4096            # Max memory usage (MB)
ANALYZER_GPU_ENABLED=true           # Enable GPU acceleration
ANALYZER_MODEL_PATH=/models         # ML model storage path

# AMQP Configuration
AMQP_CONNECTION_STRING=amqp://guest:guest@localhost:5672/
ANALYZER_QUEUE_NAME=analyzer_queue
ANALYZER_EXCHANGE_NAME=apollonia
ANALYZER_PREFETCH_COUNT=1

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/apollonia
REDIS_URL=redis://localhost:6379/0

# ML Model Configuration
TENSORFLOW_GPU_MEMORY_GROWTH=true
ESSENTIA_ALGORITHMS_PATH=/usr/local/lib/essentia
LIBROSA_CACHE_DIR=/tmp/librosa_cache

# Logging Configuration
ANALYZER_LOG_LEVEL=INFO
ANALYZER_LOG_FORMAT=json
```

### Model Configuration

```yaml
# analyzer/config/models.yml
models:
  audio:
    genre_classifier:
      version: "1.2.0"
      path: "models/genre_classifier_v1.2.0.h5"
      input_shape: [128, 128, 1]
      output_classes: 13

    mood_detector:
      version: "1.1.0"
      path: "models/mood_detector_v1.1.0.h5"
      input_shape: [128, 128, 1]
      output_dimensions: 2  # valence, arousal

    instrument_classifier:
      version: "1.0.0"
      path: "models/instrument_classifier_v1.0.0.h5"
      input_shape: [128, 128, 1]
      output_classes: 20

  video:
    scene_detector:
      version: "1.0.0"
      path: "models/scene_detector_v1.0.0.h5"
      input_shape: [224, 224, 3]

    quality_assessor:
      version: "1.0.0"
      path: "models/quality_assessor_v1.0.0.h5"
      input_shape: [224, 224, 3]

feature_extraction:
  audio:
    sample_rate: 22050
    hop_length: 512
    n_mfcc: 13
    n_chroma: 12
    n_fft: 2048

  video:
    frame_sample_rate: 1.0  # frames per second
    max_frames: 300
    resize_resolution: [224, 224]
```

## API Reference

### Internal Service API

The analyzer service primarily communicates via AMQP messages, but also provides HTTP endpoints for
monitoring and control.

#### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_loaded": 5,
  "queue_size": 12,
  "processing_active": true,
  "gpu_available": true,
  "memory_usage": {
    "used_mb": 2048,
    "total_mb": 8192,
    "percentage": 25.0
  }
}
```

#### Model Information

```http
GET /models
```

**Response:**

```json
{
  "models": [
    {
      "name": "genre_classifier",
      "version": "1.2.0",
      "type": "audio",
      "status": "loaded",
      "accuracy": 0.89,
      "classes": ["rock", "pop", "jazz", "classical", ...]
    }
  ],
  "total_models": 5,
  "memory_usage_mb": 1024
}
```

#### Processing Statistics

```http
GET /stats
```

**Response:**

```json
{
  "processed_files": 15420,
  "average_processing_time": 12.5,
  "success_rate": 0.987,
  "error_rate": 0.013,
  "queue_metrics": {
    "pending": 8,
    "processing": 2,
    "completed_today": 156
  },
  "feature_extraction_times": {
    "audio_spectral": 2.1,
    "audio_mir": 8.3,
    "video_visual": 15.2
  }
}
```

### AMQP Message Interface

#### Input Message Format

```json
{
  "message_id": "uuid",
  "file_path": "/data/music/song.mp3",
  "media_id": "media_uuid",
  "file_format": "mp3",
  "file_size": 8394752,
  "metadata": {
    "title": "Song Title",
    "artist": "Artist Name",
    "duration": 240.5
  },
  "analysis_options": {
    "extract_spectral": true,
    "extract_mir": true,
    "extract_perceptual": true,
    "similarity_analysis": true,
    "quality_assessment": true
  },
  "priority": "normal",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Output Message Format

```json
{
  "message_id": "uuid",
  "media_id": "media_uuid",
  "analysis_version": "1.0.0",
  "processing_time": 12.34,
  "success": true,
  "features": {
    "spectral": { /* spectral features */ },
    "mir": { /* MIR features */ },
    "perceptual": { /* perceptual features */ },
    "technical": { /* technical analysis */ }
  },
  "quality_metrics": {
    "snr": 45.2,
    "thd": 0.001,
    "dynamic_range": 12.5,
    "quality_score": 0.89
  },
  "similarity_vectors": {
    "spectral_vector": [0.1, 0.2, ...],
    "mir_vector": [0.3, 0.4, ...],
    "combined_vector": [0.5, 0.6, ...]
  },
  "model_versions": {
    "genre_classifier": "1.2.0",
    "mood_detector": "1.1.0"
  },
  "timestamp": "2024-01-01T12:00:12Z"
}
```

## ML Models

### Audio Models

#### Genre Classification Model

**Architecture**: Convolutional Neural Network (CNN)

- **Input**: Mel-spectrogram (128x128)
- **Output**: 13 genre classes
- **Accuracy**: 89% on test set
- **Training Data**: 50,000 labeled tracks

```python
# Model architecture
model = tf.keras.Sequential(
    [
        tf.keras.layers.Conv2D(32, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation="relu"),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(13, activation="softmax"),
    ]
)
```

#### Mood Detection Model

**Architecture**: Multi-output CNN

- **Input**: Mel-spectrogram (128x128)
- **Output**: Valence and Arousal values (0.0-1.0)
- **Training**: Regression on continuous mood labels

#### Instrument Classification Model

**Architecture**: ResNet-based CNN

- **Input**: Mel-spectrogram (128x128)
- **Output**: 20 instrument classes
- **Multi-label**: Supports multiple instruments per track

### Model Training Pipeline

```python
# analyzer/training/train_genre_model.py
import tensorflow as tf
from analyzer.data.loaders import AudioDataLoader
from analyzer.models.cnn import GenreClassifier


def train_genre_model():
    """Train genre classification model."""
    # Load training data
    data_loader = AudioDataLoader(
        data_path="/training_data/audio",
        labels_path="/training_data/labels.json",
        sample_rate=22050,
        duration=30.0,
    )

    train_dataset, val_dataset = data_loader.create_datasets(
        batch_size=32, validation_split=0.2
    )

    # Create model
    model = GenreClassifier(input_shape=(128, 128, 1), num_classes=13, dropout_rate=0.5)

    # Compile with appropriate metrics
    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy", "top_3_accuracy"],
    )

    # Training callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=10),
        tf.keras.callbacks.ModelCheckpoint(
            "models/genre_classifier_best.h5", save_best_only=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(patience=5),
    ]

    # Train model
    history = model.fit(
        train_dataset, validation_data=val_dataset, epochs=100, callbacks=callbacks
    )

    return model, history
```

### Model Deployment

```python
# analyzer/models/manager.py
class ModelManager:
    """Manages loading and versioning of ML models."""

    def __init__(self, models_config: Dict):
        self.models_config = models_config
        self.loaded_models = {}

    def load_model(self, model_name: str) -> tf.keras.Model:
        """Load a specific model."""
        config = self.models_config[model_name]
        model_path = config["path"]

        if model_name not in self.loaded_models:
            🚀 Loading model {model_name} from {model_path}
            model = tf.keras.models.load_model(model_path)
            self.loaded_models[model_name] = {
                "model": model,
                "version": config["version"],
                "loaded_at": datetime.now()
            }
            ✅ Model {model_name} loaded successfully

        return self.loaded_models[model_name]["model"]

    def predict_batch(self, model_name: str, data: np.ndarray) -> np.ndarray:
        """Run batch prediction."""
        model = self.load_model(model_name)
        return model.predict(data)
```

## Performance

### Processing Benchmarks

| Media Type     | Average Time | Throughput    | Memory Usage |
| -------------- | ------------ | ------------- | ------------ |
| MP3 (3-5 min)  | 8.2s         | 7.3 files/min | 512MB        |
| FLAC (3-5 min) | 12.1s        | 5.0 files/min | 768MB        |
| WAV (3-5 min)  | 15.3s        | 3.9 files/min | 1024MB       |
| MP4 (5-10 min) | 45.2s        | 1.3 files/min | 2048MB       |

### Optimization Strategies

#### GPU Acceleration

```python
# Enable GPU processing
import tensorflow as tf

# Configure GPU memory growth
gpus = tf.config.experimental.list_physical_devices("GPU")
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(f"⚠️ GPU configuration error: {e}")
```

#### Batch Processing

```python
# analyzer/processors/batch_processor.py
class BatchProcessor:
    """Processes multiple files in batches for efficiency."""

    def __init__(self, batch_size: int = 8):
        self.batch_size = batch_size

    async def process_batch(self, file_paths: List[str]) -> List[Dict]:
        """Process a batch of files."""
        results = []

        for i in range(0, len(file_paths), self.batch_size):
            batch = file_paths[i : i + self.batch_size]

            # Load audio files in parallel
            audio_data = await asyncio.gather(
                *[self.load_audio(path) for path in batch]
            )

            # Extract features in batch
            batch_features = self.extract_batch_features(audio_data)

            # Run ML inference in batch
            batch_predictions = self.predict_batch(batch_features)

            results.extend(batch_predictions)

        return results
```

#### Memory Management

```python
# analyzer/utils/memory.py
import gc
import psutil

class MemoryManager:
    """Manages memory usage during processing."""

    def __init__(self, max_memory_mb: int = 4096):
        self.max_memory_mb = max_memory_mb

    def check_memory_usage(self) -> float:
        """Check current memory usage percentage."""
        memory = psutil.virtual_memory()
        return memory.percent

    def cleanup_if_needed(self):
        """Perform garbage collection if memory usage is high."""
        if self.check_memory_usage() > 80:
            🧹 High memory usage detected, cleaning up...
            gc.collect()
            tf.keras.backend.clear_session()
            ✅ Memory cleanup completed
```

## Development

### Running Locally

```bash
# Install dependencies
cd analyzer
uv sync --all-extras

# Set environment variables
export AMQP_CONNECTION_STRING=amqp://guest:guest@localhost:5672/
export DATABASE_URL=postgresql://user:pass@localhost:5432/apollonia

# Run the service
uv run python -m analyzer.main

# Run with GPU support
uv run python -m analyzer.main --gpu

# Run in development mode
uv run python -m analyzer.main --debug
```

### Testing

```bash
# Run unit tests
uv run pytest tests/unit/

# Run integration tests
uv run pytest tests/integration/

# Run with test media files
uv run pytest tests/ --media-path=fixtures/media/

# Performance testing
uv run pytest tests/performance/ -m "not slow"
```

### Adding New Models

1. **Create Model Architecture**:

```python
# analyzer/models/new_model.py
class NewModel(tf.keras.Model):
    def __init__(self, **kwargs):
        super().__init__()
        # Define layers

    def call(self, inputs):
        # Forward pass
        return outputs
```

2. **Add Training Script**:

```python
# analyzer/training/train_new_model.py
def train_new_model():
    # Training logic
    pass
```

3. **Update Configuration**:

```yaml
# analyzer/config/models.yml
models:
  audio:
    new_model:
      version: "1.0.0"
      path: "models/new_model_v1.0.0.h5"
      input_shape: [128, 128, 1]
```

4. **Integrate in Processor**:

```python
# analyzer/processors/audio_processor.py
def extract_features(self, audio_data):
    # Add new model inference
    new_features = self.model_manager.predict_batch("new_model", audio_data)
    return new_features
```

### Model Versioning

```python
# analyzer/versioning/model_registry.py
class ModelRegistry:
    """Manages model versions and deployment."""

    def register_model(self, name: str, version: str, path: str, metrics: Dict):
        """Register a new model version."""
        model_info = {
            "name": name,
            "version": version,
            "path": path,
            "metrics": metrics,
            "registered_at": datetime.now(),
            "status": "active",
        }

        # Store in database
        self.db.models.insert(model_info)

    def deploy_model(self, name: str, version: str):
        """Deploy a specific model version."""
        # Update production configuration
        # Trigger service restart if needed
        pass
```

For more information on development practices, see the
[Development Guide](../development/development-guide.md) and
[Testing Guide](../development/testing.md).
