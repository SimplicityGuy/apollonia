# syntax=docker/dockerfile:1
FROM python:3.13-alpine AS builder

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set up build environment
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build

# Copy dependency files
COPY populator/pyproject.toml ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --system --no-deps -r requirements.txt

# Copy source code
COPY populator/ .

# Install the package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-deps .

# Runtime stage
FROM python:3.13-alpine

# OCI Image annotations
# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="Apollonia Populator" \
      org.opencontainers.image.description="Message consumer service that imports file metadata to Neo4j" \
      org.opencontainers.image.authors="Robert Wlodarczyk <robert@simplicityguy.com>" \
      org.opencontainers.image.url="https://github.com/SimplicityGuy/apollonia" \
      org.opencontainers.image.documentation="https://github.com/SimplicityGuy/apollonia/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/SimplicityGuy/apollonia" \
      org.opencontainers.image.vendor="Robert Wlodarczyk" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="docker.io/library/python:3.13-alpine"

# Install runtime dependencies
RUN apk add --no-cache \
    # Add any system dependencies here if needed
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S apollonia && \
    adduser -u 1001 -S apollonia -G apollonia

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/apollonia-populator /usr/local/bin/apollonia-populator

# Switch to non-root user
USER apollonia:apollonia

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Environment variables (NEO4J_PASSWORD should be provided at runtime)
ENV AMQP_CONNECTION_STRING="" \
    NEO4J_URI="bolt://localhost:7687" \
    NEO4J_USER="neo4j" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose no ports (uses AMQP and Neo4j client connections only)

# Run the service
ENTRYPOINT ["apollonia-populator"]
