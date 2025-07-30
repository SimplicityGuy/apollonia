# Apollonia ML Analyzer Service

Machine learning analysis service for processing media files in the Apollonia system.

## Overview

The analyzer service provides:

- Audio feature extraction using Essentia and Librosa
- Video analysis capabilities with MoviePy
- Machine learning models with TensorFlow
- Caching with Redis for improved performance
- Asynchronous processing via AMQP message queue

## Features

### Audio Analysis

- Tempo and beat detection
- Key and scale detection
- Genre classification
- Mood analysis
- Audio fingerprinting
- Spectral feature extraction

### Video Analysis

- Scene detection
- Frame extraction
- Motion analysis
- Object detection capabilities

## Architecture

The service uses a pipeline architecture:

1. Receives file metadata from AMQP queue
1. Loads media file for analysis
1. Extracts features using appropriate ML models
1. Caches results in Redis
1. Publishes analysis results back to AMQP

## Models

Pre-trained models are automatically downloaded and cached on first use:

- Audio genre classification
- Mood detection
- Music information retrieval

## Development

See the main project README for development setup instructions.
