# Docker Deployment Guide

This guide covers deploying Apollonia using Docker and Docker Compose.

## Quick Start

### Using Docker Compose

1. **Start all services**:

   ```bash
   docker-compose up -d
   ```

1. **View logs**:

   ```bash
   docker-compose logs -f
   ```

1. **Stop all services**:

   ```bash
   docker-compose down
   ```

## Docker Compose Configuration

### Services Overview

The `docker-compose.yml` defines four services:

```yaml
services:
  rabbitmq:    # Message broker
  neo4j:       # Graph database
  ingestor:    # File monitoring service
  populator:   # Database import service
```

### Service Dependencies

```mermaid
graph TD
    I[Ingestor] -->|depends_on| R[RabbitMQ]
    P[Populator] -->|depends_on| R
    P -->|depends_on| N[Neo4j]

    style I fill:#bbf
    style P fill:#bbf
    style R fill:#fbb
    style N fill:#bfb
```

### Volumes

Persistent data is stored in Docker volumes:

- `rabbitmq_data`: Message queue persistence
- `neo4j_data`: Graph database storage
- `neo4j_logs`: Neo4j log files
- `./data`: Host directory for file monitoring

## Individual Service Deployment

### RabbitMQ

```bash
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=apollonia \
  -e RABBITMQ_DEFAULT_PASS=apollonia \
  rabbitmq:3-management-alpine
```

Management UI: http://localhost:15672

### Neo4j

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/apollonia \
  neo4j:5-community
```

Web UI: http://localhost:7474

### Ingestor

```bash
docker run -d \
  --name apollonia-ingestor \
  -e AMQP_CONNECTION_STRING="amqp://apollonia:apollonia@rabbitmq:5672/" \
  -v $(pwd)/data:/data \
  ghcr.io/simplicityguy/apollonia/ingestor:latest
```

### Populator

```bash
docker run -d \
  --name apollonia-populator \
  -e AMQP_CONNECTION_STRING="amqp://apollonia:apollonia@rabbitmq:5672/" \
  -e NEO4J_URI="bolt://neo4j:7687" \
  -e NEO4J_USER="neo4j" \
  -e NEO4J_PASSWORD="apollonia" \
  ghcr.io/simplicityguy/apollonia/populator:latest
```

## Building Images

### Build All Services

```bash
docker-compose build
```

### Build Individual Services

```bash
# Build ingestor
docker build -t apollonia-ingestor ./ingestor

# Build populator
docker build -t apollonia-populator ./populator
```

### Build Arguments

```bash
# Build with specific Python version
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t apollonia-ingestor \
  ./ingestor
```

## Health Checks

All services include health checks:

### View Health Status

```bash
docker-compose ps
```

### Manual Health Check

```bash
# RabbitMQ
docker exec rabbitmq rabbitmq-diagnostics ping

# Neo4j
docker exec neo4j neo4j status

# Services
docker exec apollonia-ingestor python -c "import sys; sys.exit(0)"
docker exec apollonia-populator python -c "import sys; sys.exit(0)"
```

## Networking

### Default Network

Docker Compose creates a bridge network for service communication:

```bash
docker network ls | grep apollonia
```

### Service Discovery

Services can reach each other by name:

- `rabbitmq:5672`
- `neo4j:7687`

### External Access

Published ports for external access:

- RabbitMQ: `5672` (AMQP), `15672` (Management)
- Neo4j: `7474` (HTTP), `7687` (Bolt)

## Environment Configuration

### Using .env File

Create `.env` in the project root:

```env
# RabbitMQ
RABBITMQ_USER=apollonia
RABBITMQ_PASS=secure-password

# Neo4j
NEO4J_PASSWORD=secure-password

# Monitoring directory
DATA_DIRECTORY=./data
```

### Override Configuration

```bash
# Use custom compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Override environment variables
AMQP_CONNECTION_STRING="amqp://prod-server:5672/" docker-compose up
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ingestor

# Last 100 lines
docker-compose logs --tail=100 populator
```

### Resource Usage

```bash
# View resource consumption
docker stats

# Detailed inspection
docker-compose top
```

### Service Status

```bash
# Check running services
docker-compose ps

# View service details
docker inspect apollonia-ingestor
```

## Scaling

### Scale Populator Service

```bash
# Run 3 populator instances
docker-compose up -d --scale populator=3
```

### Load Balancing

Configure RabbitMQ consumer prefetch:

```python
# In populator code
channel.basic_qos(prefetch_count=1)
```

## Troubleshooting

### Common Issues

**Services won't start**:

```bash
# Check logs
docker-compose logs

# Verify port availability
netstat -tulpn | grep -E '5672|7474|7687|15672'
```

**Connection errors**:

```bash
# Test connectivity
docker-compose exec ingestor ping rabbitmq
docker-compose exec populator ping neo4j

# Check DNS resolution
docker-compose exec ingestor nslookup rabbitmq
```

**Permission issues**:

```bash
# Fix data directory permissions
chmod -R 755 ./data
chown -R 1001:1001 ./data
```

### Debugging

**Enter container shell**:

```bash
docker-compose exec ingestor sh
docker-compose exec populator sh
```

**View running processes**:

```bash
docker-compose exec ingestor ps aux
```

**Check environment**:

```bash
docker-compose exec ingestor env | grep AMQP
```

## Maintenance

### Backup

```bash
# Backup Neo4j
docker-compose exec neo4j neo4j-admin dump --to=/data/backup.dump

# Backup RabbitMQ
docker-compose exec rabbitmq rabbitmqctl export_definitions /var/lib/rabbitmq/definitions.json
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Clean system
docker system prune -a
```

## Production Considerations

### Security

1. **Change default passwords**
1. **Use secrets management**
1. **Enable TLS for connections**
1. **Run behind a firewall**

### Persistence

1. **Use named volumes**
1. **Regular backups**
1. **Monitor disk space**
1. **Configure retention policies**

### Monitoring

1. **Export metrics to Prometheus**
1. **Configure log aggregation**
1. **Set up alerts**
1. **Track service health**

### High Availability

1. **Run multiple instances**
1. **Use RabbitMQ clustering**
1. **Configure Neo4j replication**
1. **Implement health checks**
