# Configuration Guide

This guide covers all configuration options for Apollonia services.

## Environment Variables

### Ingestor Service

| Variable                 | Description                    | Default                              | Example                                |
| ------------------------ | ------------------------------ | ------------------------------------ | -------------------------------------- |
| `AMQP_CONNECTION_STRING` | AMQP broker connection URL     | `amqp://guest:guest@localhost:5672/` | `amqp://user:pass@rabbitmq:5672/vhost` |
| `DATA_DIRECTORY`         | Directory to monitor for files | `/data`                              | `/mnt/storage/incoming`                |
| `LOG_LEVEL`              | Logging verbosity              | `INFO`                               | `DEBUG`, `WARNING`, `ERROR`            |
| `PYTHONUNBUFFERED`       | Disable output buffering       | `1`                                  | `0`, `1`                               |

### Populator Service

| Variable                 | Description                | Default                              | Example                           |
| ------------------------ | -------------------------- | ------------------------------------ | --------------------------------- |
| `AMQP_CONNECTION_STRING` | AMQP broker connection URL | `amqp://guest:guest@localhost:5672/` | `amqp://user:pass@rabbitmq:5672/` |
| `NEO4J_URI`              | Neo4j connection URI       | `bolt://localhost:7687`              | `neo4j://neo4j:7687`              |
| `NEO4J_USER`             | Neo4j username             | `neo4j`                              | `apollonia_user`                  |
| `NEO4J_PASSWORD`         | Neo4j password             | `password`                           | `secure-password-123`             |
| `LOG_LEVEL`              | Logging verbosity          | `INFO`                               | `DEBUG`, `WARNING`, `ERROR`       |

### RabbitMQ Configuration

| Variable                 | Description            | Default | Example           |
| ------------------------ | ---------------------- | ------- | ----------------- |
| `RABBITMQ_DEFAULT_USER`  | Default admin username | `guest` | `apollonia`       |
| `RABBITMQ_DEFAULT_PASS`  | Default admin password | `guest` | `secure-password` |
| `RABBITMQ_DEFAULT_VHOST` | Default virtual host   | `/`     | `/apollonia`      |

### Neo4j Configuration

| Variable                           | Description                | Default       | Example                          |
| ---------------------------------- | -------------------------- | ------------- | -------------------------------- |
| `NEO4J_AUTH`                       | Authentication credentials | `neo4j/neo4j` | `neo4j/secure-password`          |
| `NEO4J_PLUGINS`                    | Plugins to install         | `[]`          | `["apoc", "graph-data-science"]` |
| `NEO4J_dbms_memory_heap_max__size` | Max heap size              | `512M`        | `2G`                             |
| `NEO4J_dbms_memory_pagecache_size` | Page cache size            | `512M`        | `1G`                             |

## Configuration Files

### Docker Compose Override

Create `docker-compose.override.yml` for local settings:

```yaml
version: '3.8'

services:
  ingestor:
    environment:
      LOG_LEVEL: DEBUG
    volumes:
      - /custom/path:/data

  populator:
    environment:
      LOG_LEVEL: DEBUG
```

### Environment File

Create `.env` file in project root:

```bash
# RabbitMQ Settings
RABBITMQ_USER=apollonia
RABBITMQ_PASS=secure-rabbitmq-password

# Neo4j Settings
NEO4J_USER=apollonia_user
NEO4J_PASSWORD=secure-neo4j-password

# Service Settings
LOG_LEVEL=INFO
DATA_DIRECTORY=./data

# Connection Strings (computed from above)
AMQP_CONNECTION_STRING=amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@rabbitmq:5672/
NEO4J_URI=bolt://neo4j:7687
```

## AMQP Configuration Details

### Connection String Format

```
amqp://[user[:password]@]host[:port][/vhost][?query-string]
```

Examples:

- `amqp://localhost` - Default guest/guest on localhost
- `amqp://user:pass@server:5672/` - With credentials
- `amqp://server:5672/myapp` - With virtual host
- `amqps://secure-server:5671/` - With TLS

### Exchange Configuration

The Apollonia exchange is configured as:

```python
exchange_declare(
    exchange="apollonia", exchange_type="fanout", durable=True, auto_delete=False
)
```

### Queue Configuration

The populator queue is configured as:

```python
queue_declare(queue="apollonia-populator", durable=True, auto_delete=False)
```

## Neo4j Configuration Details

### Connection URI Formats

- `bolt://host:7687` - Standard Bolt protocol
- `neo4j://host:7687` - Bolt with routing (for clusters)
- `bolt+s://host:7687` - Bolt with TLS
- `neo4j+s://host:7687` - Routing with TLS

### Authentication

Neo4j supports multiple authentication methods:

1. **Basic Auth** (default):

   ```python
   auth = ("username", "password")
   ```

1. **Kerberos**:

   ```python
   auth = kerberos_auth("ticket")
   ```

1. **Custom**:

   ```python
   auth = custom_auth(principal, credentials, realm, scheme)
   ```

## Logging Configuration

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about service operation
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical failures requiring immediate attention

### Log Format

Default format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example output:

```
2024-01-01 12:00:00,123 - ingestor - INFO - Starting file monitoring on /data
```

### Custom Logging

Override logging configuration:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("apollonia.log")],
)
```

## Performance Tuning

### Ingestor Performance

**File Processing**:

- Adjust hash chunk size (default: 64KB)
- Limit neighbor discovery depth
- Configure inotify watch limits

**System Limits**:

```bash
# Increase inotify watches
echo "fs.inotify.max_user_watches=524288" >> /etc/sysctl.conf
sysctl -p
```

### Populator Performance

**Message Processing**:

- Configure prefetch count for load balancing
- Adjust Neo4j connection pool size
- Enable batch processing for high volumes

**Neo4j Optimization**:

```cypher
// Create indexes for performance
CREATE INDEX file_path_index FOR (f:File) ON (f.path);
CREATE INDEX file_sha256_index FOR (f:File) ON (f.sha256);
```

### RabbitMQ Performance

**Memory Settings**:

```bash
# High memory usage
RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="-rabbitmq_management load_definitions '/etc/rabbitmq/definitions.json' +P 1048576"
```

**Connection Limits**:

```erlang
[
  {rabbit, [
    {tcp_listeners, [5672]},
    {num_acceptors.tcp, 10},
    {connection_max, infinity}
  ]}
].
```

## Security Configuration

### TLS/SSL Setup

**RabbitMQ TLS**:

```yaml
environment:
  RABBITMQ_SSL_CERTFILE: /certs/server_certificate.pem
  RABBITMQ_SSL_KEYFILE: /certs/server_key.pem
  RABBITMQ_SSL_CACERTFILE: /certs/ca_certificate.pem
```

**Neo4j TLS**:

```yaml
environment:
  NEO4J_dbms_ssl_policy_bolt_enabled: "true"
  NEO4J_dbms_ssl_policy_bolt_base__directory: /ssl/bolt
```

### Secrets Management

**Docker Secrets**:

```yaml
services:
  populator:
    environment:
      NEO4J_PASSWORD_FILE: /run/secrets/neo4j_password
    secrets:
      - neo4j_password

secrets:
  neo4j_password:
    external: true
```

**Kubernetes Secrets**:

```yaml
env:
  - name: NEO4J_PASSWORD
    valueFrom:
      secretKeyRef:
        name: apollonia-secrets
        key: neo4j-password
```

## Monitoring Configuration

### Prometheus Metrics

**RabbitMQ Metrics**:

```yaml
services:
  rabbitmq:
    ports:
      - "15692:15692"  # Prometheus metrics
```

**Custom Metrics**:

```python
from prometheus_client import Counter, Histogram

files_processed = Counter("apollonia_files_processed_total", "Total files processed")
processing_time = Histogram(
    "apollonia_processing_duration_seconds", "File processing duration"
)
```

### Health Check Configuration

**Docker Health Checks**:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Production Configuration Checklist

- [ ] Change all default passwords
- [ ] Enable TLS for all connections
- [ ] Configure resource limits
- [ ] Set up monitoring and alerting
- [ ] Enable audit logging
- [ ] Configure backup schedules
- [ ] Set retention policies
- [ ] Test disaster recovery
- [ ] Document custom configuration
- [ ] Review security settings
