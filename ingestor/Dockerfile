# Build stage
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY ingestor/pyproject.toml .

# Create package directory and copy source
RUN mkdir -p ingestor
COPY ingestor/__init__.py ingestor/
COPY ingestor/__main__.py ingestor/
COPY ingestor/*.py ingestor/

# Install dependencies
RUN uv venv && \
    uv pip install -e .

# Runtime stage
FROM python:3.12-slim

# Install runtime dependencies including gosu for user switching
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 apollonia

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=apollonia:apollonia /app/.venv /app/.venv

# Copy application code
COPY --from=builder --chown=apollonia:apollonia /app ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default environment variables
ENV AMQP_CONNECTION_STRING=""
ENV DATA_DIRECTORY="/data"

# Create data directory
RUN mkdir -p /data && chown apollonia:apollonia /data

# Copy entrypoint script to handle permissions
COPY ingestor/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Volume for monitored data
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Labels
LABEL org.opencontainers.image.title="Apollonia Ingestor"
LABEL org.opencontainers.image.description="File monitoring service that publishes file metadata to AMQP"
LABEL org.opencontainers.image.authors="robert@simplicityguy.com"
LABEL org.opencontainers.image.source="https://github.com/SimplicityGuy/apollonia"

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "ingestor"]
