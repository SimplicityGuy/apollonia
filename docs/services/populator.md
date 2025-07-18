# Populator Service

The Populator service consumes file metadata messages from AMQP and imports them into a Neo4j graph
database.

## Overview

The Populator acts as a bridge between the message queue and the graph database. It:

1. Connects to RabbitMQ and Neo4j
1. Consumes messages from the queue
1. Parses file metadata
1. Creates or updates nodes in Neo4j
1. Establishes relationships between files

## Configuration

### Environment Variables

| Variable                 | Description                | Default                              | Required |
| ------------------------ | -------------------------- | ------------------------------------ | -------- |
| `AMQP_CONNECTION_STRING` | AMQP broker connection URL | `amqp://guest:guest@localhost:5672/` | No       |
| `NEO4J_URI`              | Neo4j connection URI       | `bolt://localhost:7687`              | No       |
| `NEO4J_USER`             | Neo4j username             | `neo4j`                              | No       |
| `NEO4J_PASSWORD`         | Neo4j password             | `password`                           | Yes\*    |

\*Password should be changed in production

### AMQP Configuration

- **Exchange Name**: `apollonia`
- **Queue Name**: `apollonia-populator`
- **Queue Properties**: `durable=True`, `auto_delete=False`
- **Routing Key**: `file.created`
- **Consumer Mode**: Automatic acknowledgment on success

## Implementation Details

### Message Processing

The service processes messages containing:

```json
{
    "file_path": "/data/example.txt",
    "event_type": "IN_CREATE",
    "sha256_hash": "abc123...",
    "xxh128_hash": "def456...",
    "size": 1024,
    "modified_time": "2024-01-01T12:00:00+00:00",
    "accessed_time": "2024-01-01T12:00:00+00:00",
    "changed_time": "2024-01-01T12:00:00+00:00",
    "timestamp": "2024-01-01T12:00:00+00:00",
    "neighbors": ["file1.txt", "file2.log"]
}
```

### Neo4j Data Model

#### File Node

```cypher
(:File {
    path: String,        // Unique file path
    sha256: String,      // SHA-256 hash
    xxh128: String,      // xxHash128
    size: Integer,       // File size in bytes
    modified: DateTime,  // Last modification time
    accessed: DateTime,  // Last access time
    changed: DateTime,   // Last status change
    discovered: DateTime,// When first seen
    event_type: String   // File system event type
})
```

#### Relationships

```cypher
// Neighbor relationship (bidirectional)
(:File)-[:NEIGHBOR]->(:File)
```

### Database Operations

#### Node Creation/Update

```cypher
MERGE (f:File {path: $file_path})
SET f.sha256 = $sha256_hash,
    f.xxh128 = $xxh128_hash,
    f.size = $size,
    f.modified = datetime($modified_time),
    f.accessed = datetime($accessed_time),
    f.changed = datetime($changed_time),
    f.discovered = datetime($timestamp),
    f.event_type = $event_type
RETURN f
```

#### Relationship Creation

```cypher
MERGE (f1:File {path: $file_path})
MERGE (f2:File {path: $neighbor_path})
MERGE (f1)-[:NEIGHBOR]->(f2)
```

## Docker Deployment

### Dockerfile Features

- **Base Image**: `python:3.13-alpine`
- **Multi-stage Build**: Optimized size
- **Non-root User**: Security best practice
- **Health Check**: Service availability
- **No Volumes**: Stateless service

### Building the Image

```bash
docker build -t apollonia-populator ./populator
```

### Running the Container

```bash
docker run -d \
  --name apollonia-populator \
  -e AMQP_CONNECTION_STRING="amqp://user:pass@rabbitmq:5672/" \
  -e NEO4J_URI="bolt://neo4j:7687" \
  -e NEO4J_USER="neo4j" \
  -e NEO4J_PASSWORD="secure-password" \
  apollonia-populator
```

## Development

### Running Locally

```bash
# Set environment variables
export AMQP_CONNECTION_STRING="amqp://localhost:5672/"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="apollonia"

# Run the service
uv run task populator
```

### Code Structure

```python
populator/
├── __init__.py          # Package initialization
├── populator.py         # Main service implementation
└── pyproject.toml       # Package configuration
```

### Key Classes

#### `Populator`

Main service class with:

- `__aenter__` / `__aexit__`: Async context manager for connections
- `consume()`: Main message consumption loop
- `process_message()`: Individual message handler
- `_import_to_neo4j()`: Database import logic
- `stop()`: Graceful shutdown

## Error Handling

### Connection Management

- **AMQP**: Uses `aio_pika` with robust connections
- **Neo4j**: Async driver with connection pooling
- **Retry Logic**: Automatic reconnection on failures

### Message Processing

- Failed messages are not acknowledged
- RabbitMQ will redeliver failed messages
- Errors are logged with full context
- Individual failures don't stop the service

### Graceful Shutdown

- Handles SIGINT and SIGTERM
- Completes current message processing
- Closes all connections cleanly

## Performance Considerations

### Throughput

- Processes messages sequentially
- Can scale horizontally with multiple instances
- Neo4j operations are the primary bottleneck

### Resource Usage

- Low memory footprint
- CPU usage depends on message rate
- Network I/O for both AMQP and Neo4j

### Optimization Tips

- Use Neo4j connection pooling
- Batch similar operations when possible
- Consider parallel processing for high volumes
- Monitor Neo4j query performance

## Monitoring

### Logging

The service logs:

- Service lifecycle events
- Connection establishment
- Message processing results
- Errors with stack traces

### Metrics to Monitor

- Messages processed per minute
- Neo4j query execution time
- Queue depth and consumption rate
- Connection stability

### Health Indicators

- AMQP connection status
- Neo4j connection status
- Message processing success rate
- Last successful message timestamp

## Neo4j Queries

### Useful Queries

**Count all files**:

```cypher
MATCH (f:File) RETURN count(f) as fileCount
```

**Find files by hash**:

```cypher
MATCH (f:File {sha256: $hash})
RETURN f
```

**Find duplicate files**:

```cypher
MATCH (f1:File), (f2:File)
WHERE f1.sha256 = f2.sha256 AND f1.path <> f2.path
RETURN f1.path, f2.path, f1.sha256
```

**File neighbor network**:

```cypher
MATCH (f:File {path: $path})-[:NEIGHBOR]-(n:File)
RETURN f, n
```

**Recently discovered files**:

```cypher
MATCH (f:File)
WHERE f.discovered > datetime() - duration('PT1H')
RETURN f ORDER BY f.discovered DESC
```

## Troubleshooting

### Common Issues

**Cannot connect to RabbitMQ**:

- Verify AMQP connection string
- Check network connectivity
- Ensure RabbitMQ is running
- Verify credentials

**Neo4j connection failures**:

- Check Neo4j is running
- Verify bolt protocol is enabled
- Test credentials
- Check firewall rules

**Messages not being processed**:

- Check queue has messages
- Verify queue binding
- Look for processing errors in logs
- Check message format

**High memory usage**:

- Monitor message accumulation
- Check for Neo4j query issues
- Verify connection pooling
- Look for memory leaks

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
export NEO4J_DEBUG=true
uv run task populator
```

## Security Considerations

- Store Neo4j credentials securely
- Use TLS for Neo4j connections in production
- Run as non-root user
- No ports exposed by the service
- Validate message content before processing

## Scaling Strategies

### Horizontal Scaling

Run multiple populator instances:

```yaml
deploy:
  replicas: 3
```

### Queue Configuration

- Configure prefetch count for load balancing
- Use message TTL for old messages
- Implement dead letter queues

### Neo4j Optimization

- Use indexes on frequently queried properties
- Consider Neo4j clustering for high loads
- Optimize Cypher queries
- Use batch operations where possible
