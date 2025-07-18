# Ingestor Service

The Ingestor service monitors a directory for file system events and publishes file metadata to an
AMQP message queue.

## Overview

The Ingestor uses Linux's inotify system to efficiently monitor file system events. When files are
created, moved, or modified in the watched directory, the service:

1. Detects the file system event
1. Extracts comprehensive metadata
1. Computes cryptographic hashes
1. Discovers related files
1. Publishes the information to AMQP

## Configuration

### Environment Variables

| Variable                 | Description                    | Default                              | Required |
| ------------------------ | ------------------------------ | ------------------------------------ | -------- |
| `AMQP_CONNECTION_STRING` | AMQP broker connection URL     | `amqp://guest:guest@localhost:5672/` | No       |
| `DATA_DIRECTORY`         | Directory to monitor for files | `/data`                              | No       |

### AMQP Configuration

- **Exchange Name**: `apollonia`
- **Exchange Type**: `fanout`
- **Exchange Properties**: `durable=True`, `auto_delete=False`
- **Routing Key**: `file.created`
- **Message Delivery**: Persistent (`delivery_mode=2`)

## Implementation Details

### File Monitoring

The service uses `asyncinotify` to monitor these events:

- `IN_CREATE`: New file created
- `IN_MOVED_TO`: File moved into directory
- `IN_CLOSE_WRITE`: File closed after writing

### Metadata Extraction

The `Prospector` class extracts:

```python
{
    "file_path": str,  # Absolute path to file
    "event_type": str,  # Type of file system event
    "sha256_hash": str,  # SHA-256 hash of file contents
    "xxh128_hash": str,  # xxHash128 for fast comparison
    "size": int,  # File size in bytes
    "modified_time": str,  # ISO 8601 timestamp
    "accessed_time": str,  # ISO 8601 timestamp
    "changed_time": str,  # ISO 8601 timestamp
    "timestamp": str,  # Event timestamp
    "neighbors": List[str],  # Related files
}
```

### Hash Computation

Files are hashed using:

- **SHA-256**: Cryptographic hash for integrity
- **xxHash128**: Fast non-cryptographic hash for deduplication

Hashing is performed in 64KB chunks for memory efficiency.

### Neighbor Discovery

The service identifies related files by:

1. Files with the same stem but different extensions
1. Common metadata files (tracklist, tracks, info, readme)
1. Files starting with the same 3-character prefix

Maximum of 10 neighbors are returned per file.

## Docker Deployment

### Dockerfile Features

- **Base Image**: `python:3.13-alpine` (minimal size)
- **Multi-stage Build**: Separate build and runtime stages
- **Non-root User**: Runs as `apollonia` user (UID 1001)
- **Health Check**: Python-based liveness check
- **Volume**: `/data` for monitored files

### Building the Image

```bash
docker build -t apollonia-ingestor ./ingestor
```

### Running the Container

```bash
docker run -d \
  --name apollonia-ingestor \
  -e AMQP_CONNECTION_STRING="amqp://user:pass@rabbitmq:5672/" \
  -v /path/to/files:/data \
  apollonia-ingestor
```

## Development

### Running Locally

```bash
# Set environment variables
export AMQP_CONNECTION_STRING="amqp://localhost:5672/"
export DATA_DIRECTORY="./data"

# Run the service
uv run task ingestor
```

### Code Structure

```python
ingestor/
├── __init__.py          # Package initialization
├── ingestor.py          # Main service class and entry point
├── prospector.py        # File metadata extraction
└── pyproject.toml       # Package configuration
```

### Key Classes

#### `Ingestor`

Main service class implementing:

- `__enter__` / `__exit__`: Context manager for AMQP connection
- `ingest()`: Main event loop for file monitoring
- `stop()`: Graceful shutdown handler

#### `Prospector`

File analysis class providing:

- `prospect()`: Extract all file metadata
- `_compute_hashes()`: Calculate file hashes
- `_find_neighbors()`: Discover related files

## Error Handling

### Connection Failures

- AMQP connection errors are logged and cause service exit
- Reconnection should be handled by container orchestration

### File Processing Errors

- Individual file errors are logged but don't stop the service
- Failed files can be reprocessed on next event

### Graceful Shutdown

- Handles SIGINT and SIGTERM signals
- Closes AMQP connection cleanly
- Completes in-progress operations

## Performance Considerations

### Memory Usage

- Files are hashed in 64KB chunks
- No full file loading into memory
- Efficient for large files

### CPU Usage

- xxHash128 is optimized for speed
- SHA-256 uses native implementations
- Async I/O prevents blocking

### Network Usage

- Messages are JSON-encoded
- Typical message size: 1-2KB
- Persistent delivery adds overhead

## Monitoring

### Logging

The service logs:

- Service startup/shutdown
- AMQP connection events
- File processing events
- Errors with full context

### Metrics to Monitor

- Files processed per minute
- Message publish success rate
- Hash computation time
- AMQP connection stability

### Health Checks

Docker health check verifies:

- Python runtime is responsive
- Service hasn't crashed
- Basic functionality works

## Troubleshooting

### Common Issues

**No files detected**:

- Check `DATA_DIRECTORY` exists and is readable
- Verify inotify watches aren't exhausted
- Ensure files are being written to the correct directory

**AMQP connection failures**:

- Verify `AMQP_CONNECTION_STRING` is correct
- Check RabbitMQ is running and accessible
- Look for authentication errors in logs

**High memory usage**:

- Check for very large files being processed
- Monitor number of neighbors being tracked
- Verify hash computation isn't hanging

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uv run task ingestor
```

## Security Considerations

- Runs as non-root user in container
- No network ports exposed
- File access limited to mounted volume
- AMQP credentials should use secrets management
