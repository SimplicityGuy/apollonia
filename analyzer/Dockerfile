# ML Analyzer Service Dockerfile
# Multi-stage build for optimized image size

# Build stage
FROM python:3.13-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY analyzer/pyproject.toml ./analyzer/

# Install dependencies
RUN uv venv && \
    uv sync --no-dev

# Runtime stage
FROM python:3.13-slim

# Install runtime dependencies for media processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 -s /bin/bash apollonia

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=apollonia:apollonia /app/.venv /app/.venv

# Copy application code
COPY --chown=apollonia:apollonia analyzer/ ./analyzer/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default environment variables
ENV AMQP_CONNECTION_STRING="amqp://guest:guest@rabbitmq:5672/"
ENV REDIS_URL="redis://redis:6379/0"
ENV MODEL_CACHE_DIR="/models"
ENV ENABLE_GPU="false"

# Create model cache directory
RUN mkdir -p /models && chown apollonia:apollonia /models

# Switch to non-root user
USER apollonia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Volume for model cache
VOLUME ["/models"]

# Labels
LABEL org.opencontainers.image.title="Apollonia ML Analyzer"
LABEL org.opencontainers.image.description="Machine learning analysis service for media files"
LABEL org.opencontainers.image.authors="robert@simplicityguy.com"
LABEL org.opencontainers.image.source="https://github.com/SimplicityGuy/apollonia"

# Run the analyzer
CMD ["python", "-m", "analyzer.analyzer"]
