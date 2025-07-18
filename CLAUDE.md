# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Apollonia is a Python-based microservices architecture for file monitoring and processing, using AMQP message queuing for service communication. The project consists of two main services:

1. **Ingestor**: Monitors the `/data` directory for new files and publishes file metadata to AMQP
2. **Populator**: Consumes messages from AMQP queue (appears designed for Neo4j import based on dependencies)

## Development Commands

### Code Quality
```bash
# Install pre-commit hooks (required for development)
pre-commit install

# Run pre-commit checks manually
pre-commit run --all-files

# Format code with Black
black . --line-length 100

# Sort imports
isort . --profile black
```

### Docker Operations
```bash
# Build individual services
docker build -t apollonia-ingestor ./ingestor
docker build -t apollonia-populator ./populator

# Run services (requires AMQP_CONNECTION_STRING environment variable)
docker run -e AMQP_CONNECTION_STRING="amqp://user:password@localhost:5672/" apollonia-ingestor
docker run -e AMQP_CONNECTION_STRING="amqp://user:password@localhost:5672/" apollonia-populator
```

### Testing
```bash
# Currently no test framework is set up
# When implementing tests, consider using pytest with async support
```

## Architecture

### Service Communication
- Services communicate via AMQP using a fan-out exchange named "apollonia"
- Messages are JSON-encoded file metadata with persistent delivery mode
- The ingestor publishes to the exchange, populator consumes from its queue

### Key Design Patterns
1. **Asynchronous Processing**: Both services use async/await patterns
2. **Event-Driven Architecture**: File system events trigger the processing pipeline
3. **Context Manager Pattern**: Clean resource management (see Ingestor class)
4. **Microservices**: Loosely coupled services with message queue communication

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
- Uses `asyncinotify` for file system monitoring
- Implements file "prospecting" to find related files (neighbors)
- Computes both SHA256 and xxh128 hashes for files
- Handles inotify events: IN_CREATE, IN_MOVED_TO

#### Populator (`/populator/`)
- Basic structure exists but core functionality needs implementation
- Configured for Neo4j integration (see dependencies)
- Should implement message consumption and Neo4j import logic

## Important Implementation Details

1. **File Watching**: The ingestor monitors `/data` directory inside the container
2. **Error Handling**: Both services implement graceful shutdown on SIGINT/SIGTERM
3. **Message Persistence**: AMQP messages use delivery_mode=2 for persistence
4. **Non-Root Execution**: Docker containers run as non-root user (UID 1001)
5. **Multi-Platform Support**: CI builds for linux/amd64 and linux/arm64

## Current Development State

- Ingestor service is mostly complete with file monitoring and metadata extraction
- Populator service needs implementation of the message consumption and Neo4j import logic
- No test suite exists yet - consider adding pytest with async support
- GitHub Actions CI/CD pipeline is configured with security scanning
