# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project Overview

Apollonia is a comprehensive Python 3.12 media catalog system that automatically detects,
classifies, and analyzes audio and video files using machine learning. Built with a modern
microservices architecture, it provides real-time processing, advanced analytics, and a responsive
web interface for managing large media collections. The project consists of several main services:

1. **Ingestor**: Monitors directories for new media files and publishes file metadata to AMQP
1. **Populator**: Consumes messages from AMQP queue and stores file metadata in PostgreSQL and Neo4j
1. **Analyzer**: Performs ML-based analysis on audio/video files using TensorFlow and Essentia
1. **API**: Provides REST and GraphQL endpoints with JWT authentication for accessing the catalog
1. **Frontend**: React 18 TypeScript web interface with real-time updates for browsing and managing
   media

## Development Commands

### Setup and Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Complete development setup (installs dependencies and pre-commit hooks)
uv run task install

# Alternative: manual setup
uv sync --all-extras
uv run task install-hooks
```

### Code Quality

```bash
# Format code with Ruff
uv run task format

# Run linting checks
uv run task lint

# Run type checking
uv run task typecheck

# Run all quality checks
uv run task check

# Run pre-commit on all files
uv run task check-all
```

### Docker Operations

```bash
# Build all services with docker-compose
uv run task build-docker

# Start all services (RabbitMQ, Neo4j, Ingestor, Populator)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Build individual services
docker build -t apollonia-ingestor ./ingestor
docker build -t apollonia-populator ./populator
```

### Testing

```bash
# Run tests with coverage
uv run task test

# Run tests in watch mode
uv run task test-watch

# Run integration tests only
uv run task test-integration

# Run end-to-end tests only
uv run task test-e2e

# Run specific test file
uv run pytest tests/test_ingestor.py -v

# Run tests for a specific Python version
uv run --python 3.12 pytest
```

### Development Tasks

```bash
# Run the ingestor locally
uv run task ingestor

# Run the populator locally
uv run task populator

# Build Python packages (main project)
uv run task build

# Build individual service packages
uv run task build-services

# Clean build artifacts
uv run task clean

# Complete cleanup (including Docker)
uv run task clean-all

# Update pre-commit hooks
uv run task update-hooks

# Run CI checks locally
uv run task ci
```

## Required Environment Variables

### Ingestor

- `AMQP_CONNECTION_STRING`: AMQP broker URL (default: `amqp://guest:guest@localhost:5672/`)
- `DATA_DIRECTORY`: Directory to monitor for files (default: `/data`)

### Populator

- `AMQP_CONNECTION_STRING`: AMQP broker URL (default: `amqp://guest:guest@localhost:5672/`)
- `DATABASE_URL`: PostgreSQL connection URL (default:
  `postgresql://postgres:password@localhost:5432/apollonia`)
- `NEO4J_URI`: Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (required, no default)

### API Service

- `DATABASE_URL`: PostgreSQL connection URL
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: `30`)

### Analyzer

- `AMQP_CONNECTION_STRING`: AMQP broker URL
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)
- `ML_MODEL_PATH`: Path to ML models directory

## Architecture

### Service Communication

- Services communicate via AMQP using a fan-out exchange named "apollonia"
- Messages are JSON-encoded file metadata with persistent delivery mode
- The ingestor publishes to the exchange, populator consumes from its queue

### Key Design Patterns

1. **Asynchronous Processing**: Both services use async/await patterns
1. **Event-Driven Architecture**: File system events trigger the processing pipeline
1. **Context Manager Pattern**: Clean resource management (see Ingestor class)
1. **Microservices**: Loosely coupled services with message queue communication

### Message Format

The ingestor publishes messages with this structure:

```json
{
  "file_path": "/data/example.txt",
  "event_type": "IN_CREATE",
  "sha256_hash": "...",
  "xxh128_hash": "...",
  "modified_time": "2024-01-01T00:00:00.000000",
  "accessed_time": "2024-01-01T00:00:00.000000",
  "changed_time": "2024-01-01T00:00:00.000000",
  "neighbors": ["example.txt.meta", "example.txt.bak"]
}
```

### Service-Specific Notes

#### Ingestor (`/ingestor/`)

- Uses `watchdog` for cross-platform file system monitoring
- Implements file "prospecting" to find related files (neighbors)
- Computes both SHA256 and xxh128 hashes for files
- Handles file events: creation, modification, and movement

#### Populator (`/populator/`)

- Complete AMQP message consumption with asyncio patterns
- PostgreSQL integration for primary data storage with SQLAlchemy
- Neo4j integration for graph relationships and advanced queries
- Implements comprehensive media metadata storage and indexing

## Important Implementation Details

1. **File Watching**: The ingestor monitors `/data` directory inside the container
1. **Error Handling**: Both services implement graceful shutdown on SIGINT/SIGTERM
1. **Message Persistence**: AMQP messages use delivery_mode=2 for persistence
1. **Non-Root Execution**: Docker containers run as non-root user (UID 1001)
1. **Platform Support**: CI builds for linux/amd64 only

## Current Development State

- **Ingestor service**: Complete with async file monitoring, hashing, and AMQP publishing
- **Populator service**: Complete with AMQP consumption and Neo4j graph import
- **Analyzer service**: ML models for audio/video analysis with TensorFlow/Essentia integration
- **API service**: FastAPI with REST endpoints and Strawberry GraphQL
- **Frontend**: React 18 with TypeScript, Tailwind CSS, and real-time updates
- **Development tooling**: Modern Python setup with uv, ruff, mypy, and taskipy
- **Docker**: Multi-stage builds with OCI-compliant labels and health checks
- **CI/CD**: GitHub Actions with Python testing, security scanning, and x86_64 builds
- **Testing**: Comprehensive test suite with unit, integration, and E2E tests

## CI/CD Pipeline

### GitHub Actions Workflows

The project uses optimized GitHub Actions workflows with performance enhancements:

- **Reusable Actions**: `.github/actions/setup-python-env` and `setup-frontend-env`
- **Smart Testing**: Change detection skips unnecessary tests
- **Parallel Execution**: Tests run concurrently by type
- **Comprehensive Caching**: Dependencies, Docker layers, and test results
- **Timeouts**: All jobs have appropriate timeouts to prevent hanging

### Workflow Commands

```bash
# Run workflows manually
gh workflow run test.yml                              # Force test run
gh workflow run docker.yml -f push_images=true        # Build and push images
gh workflow run dependencies.yml -f update_type=minor # Update dependencies

# View workflow status
gh run list --workflow=test.yml
gh run view <run-id> --log

# Download artifacts
gh run download <run-id> -n pytest-results-unit-py3.12
```

## Development Workflow

1. **Local Development**:

   ```bash
   # Start dependencies
   docker-compose up -d rabbitmq neo4j

   # Run services locally
   uv run task ingestor  # In one terminal
   uv run task populator # In another terminal
   ```

1. **Before Committing**:

   ```bash
   uv run task check-all  # Run all quality checks
   ```

1. **Testing Changes**:

   ```bash
   docker-compose build
   docker-compose up
   # Copy test files to ./data directory
   ```

## Test-Specific Guidelines

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test categories
uv run pytest -m "not integration and not e2e"  # Unit tests only
uv run pytest -m integration                     # Integration tests
uv run pytest -m e2e                            # End-to-end tests

# Run tests for specific service
uv run pytest tests/unit/test_ingestor.py
uv run pytest tests/unit/test_populator.py

# Frontend tests
cd frontend && npm test
```

### Platform-Specific Notes

- **watchdog**: Cross-platform file monitoring library that works on Linux, macOS, and Windows
- **Docker tests**: Require Docker to be running. Use `@pytest.mark.docker` marker
- **Integration tests**: May require services (RabbitMQ, Neo4j) to be running

### Test Structure

```
tests/
├── unit/               # Fast, isolated unit tests
├── integration/        # Tests requiring service dependencies
├── e2e/               # End-to-end tests with full stack
├── fixtures.py        # Shared test fixtures and utilities
└── conftest.py        # pytest configuration
```

## Important Development Guidelines

When working with this codebase:

1. **Preserve test functionality** - Ensure tests continue to pass after changes
1. **Handle platform differences** - Add appropriate skip markers for platform-specific code
1. **Use existing patterns** - Follow the project's established testing patterns
1. **Minimize pragma usage** - Only use `# noqa` comments when absolutely necessary
1. **Document why** - When adding pragmas or workarounds, explain why they're needed
1. **Run quality checks** - Always run `uv run task check-all` before committing
1. **Update documentation** - Keep docs in sync with code changes
