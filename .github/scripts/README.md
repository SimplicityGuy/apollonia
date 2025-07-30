# GitHub Actions Scripts

This directory contains helper scripts used by GitHub Actions workflows.

## health-check.sh

Enhanced health check script for Docker Compose services with consecutive failure tracking.

### Features

- Tracks consecutive unhealthy checks per container
- Aborts early if any container is unhealthy for 3+ consecutive checks
- Provides detailed diagnostics for failing services
- Shows service-specific logs for unhealthy containers
- Color-coded output for better visibility

### Usage

```bash
# Basic usage (uses default settings)
./.github/scripts/health-check.sh

# Custom configuration via environment variables
MAX_RETRIES=120 CHECK_INTERVAL=10 MAX_CONSECUTIVE_UNHEALTHY=5 ./.github/scripts/health-check.sh
```

### Configuration

- `MAX_RETRIES`: Maximum number of health check attempts (default: 60)
- `CHECK_INTERVAL`: Seconds between health checks (default: 5)
- `MAX_CONSECUTIVE_UNHEALTHY`: Maximum consecutive unhealthy checks before abort (default: 3)

### Exit Codes

- `0`: All services became healthy
- `1`: Services failed to become healthy or exceeded consecutive unhealthy threshold

### Example Output

```
⏳ Waiting for services to become healthy...
Configuration: MAX_RETRIES=60, CHECK_INTERVAL=5, MAX_CONSECUTIVE_UNHEALTHY=3

✅ apollonia-frontend: state=running, health=healthy
✅ apollonia-api: state=running, health=healthy
⚠️  apollonia-analyzer: state=running, health=starting
✅ apollonia-rabbitmq: state=running, health=healthy
✅ apollonia-postgres: state=running, health=healthy
✅ apollonia-neo4j: state=running, health=healthy
✅ apollonia-redis: state=running, health=no health check
✅ Healthy: 6/7 services

Retry 1/60 - Waiting 5s before next check...
---
```
