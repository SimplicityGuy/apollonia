# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS builder

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set up build environment
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build

# Copy dependency files
COPY ingestor/pyproject.toml ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system --no-deps -r requirements.txt

# Copy source code
COPY ingestor/ .

# Install the package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-deps .

# Runtime stage
FROM python:3.12-alpine

# OCI Image annotations
# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="Apollonia Ingestor" \
      org.opencontainers.image.description="File monitoring service that publishes file metadata to AMQP" \
      org.opencontainers.image.authors="Robert Wlodarczyk <robert@simplicityguy.com>" \
      org.opencontainers.image.url="https://github.com/SimplicityGuy/apollonia" \
      org.opencontainers.image.documentation="https://github.com/SimplicityGuy/apollonia/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/SimplicityGuy/apollonia" \
      org.opencontainers.image.vendor="Robert Wlodarczyk" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="docker.io/library/python:3.12-alpine"

# Install runtime dependencies
RUN apk add --no-cache \
    # Add any system dependencies here if needed
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S apollonia && \
    adduser -u 1001 -S apollonia -G apollonia

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/apollonia-ingestor /usr/local/bin/apollonia-ingestor

# Create data directory
RUN mkdir -p /data && \
    chown -R apollonia:apollonia /data

# Switch to non-root user
USER apollonia:apollonia

# Set working directory
WORKDIR /app

# Volume for monitored data
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Environment variables
ENV AMQP_CONNECTION_STRING="" \
    DATA_DIRECTORY="/data" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose no ports (uses AMQP client connection only)

# Run the service
ENTRYPOINT ["apollonia-ingestor"]
