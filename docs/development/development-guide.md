# Development Guide

This guide covers the development setup and workflow for the Apollonia project.

## Prerequisites

- **Python 3.12** (required for TensorFlow and Essentia compatibility)
- **Node.js 22+** (for frontend development)
- **Docker and Docker Compose** (v2.0+)
- **uv package manager** (modern Python package management)
- **Just** (optional but recommended for task running)
- **Git** (version control)

## Initial Setup

### 1. Install uv Package Manager

uv is a fast Python package and project manager written in Rust:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup the Repository

```bash
git clone https://github.com/SimplicityGuy/apollonia.git
cd apollonia

# Install all dependencies including dev tools
uv sync --all-extras

# Install pre-commit hooks
uv run task install-hooks
```

## Development Commands

All development tasks are managed through taskipy. Run `uv run task --list` to see available tasks.

### Code Quality

```bash
# Format code with Ruff
uv run task format

# Run linting checks
uv run task lint

# Run type checking with mypy
uv run task typecheck

# Run all quality checks
uv run task check

# Run pre-commit on all files
uv run task check-all
```

### Testing

```bash
# Run tests with coverage
uv run task test

# Run tests in watch mode
uv run task test-watch

# Run specific test file
uv run pytest tests/test_ingestor.py -v
```

### Running Services Locally

```bash
# Using Just (recommended)
just up-infra      # Start infrastructure services
just ingestor      # Run the ingestor service
just analyzer      # Run the analyzer service
just populator     # Run the populator service
just api           # Run the API service
just frontend      # Run the frontend development server

# Or manually with Docker Compose
docker-compose up -d postgres rabbitmq redis neo4j

# Run services individually with uv
uv run task ingestor
uv run task populator
uv run task api

# Frontend development
cd frontend && npm run dev
```

### Building and Docker

```bash
# Build Python packages
uv run task build

# Build Docker images
uv run task build-docker

# Start all services with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Project Structure

```
apollonia/
├── ingestor/              # File monitoring service
│   ├── ingestor.py       # Main service entry point
│   ├── media_ingestor.py # Enhanced media-specific ingestion
│   ├── prospector.py     # File metadata extraction
│   ├── media_prospector.py # Media-specific metadata
│   ├── media_utils.py    # Media processing utilities
│   ├── pyproject.toml    # Package configuration
│   └── Dockerfile
├── analyzer/             # ML analysis service
│   ├── analyzer.py       # Main service entry point
│   ├── ml/               # Machine learning models
│   │   ├── extractors.py # Feature extraction
│   │   ├── pipelines.py  # Processing pipelines
│   │   └── real_models.py # TensorFlow/Essentia models
│   ├── processors.py     # Media processors
│   ├── cache.py          # Result caching
│   └── Dockerfile
├── populator/            # Database import service
│   ├── populator.py      # Main service entry point
│   ├── pyproject.toml    # Package configuration
│   └── Dockerfile
├── api/                  # REST/GraphQL API service
│   ├── main.py           # FastAPI application
│   ├── endpoints/        # REST endpoints
│   ├── graphql/          # GraphQL schema
│   ├── database.py       # Database connections
│   └── Dockerfile
├── frontend/             # React web application
│   ├── src/              # Source code
│   ├── package.json      # Node dependencies
│   ├── vite.config.ts    # Build configuration
│   └── Dockerfile
├── database/             # Database migrations
│   ├── models.py         # SQLAlchemy models
│   ├── alembic/          # Migration scripts
│   └── pyproject.toml
├── shared/               # Shared utilities
│   └── logging_utils.py  # Logging configuration
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── fixtures/         # Test fixtures
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── justfile              # Task runner commands
├── pyproject.toml        # Root project configuration
├── docker-compose.yml    # Local development environment
└── .pre-commit-config.yaml
```

## Code Style and Standards

The project uses:

- **Ruff** for linting and formatting (replaces Black, isort, Flake8, etc.)
- **mypy** for static type checking
- **pytest** for testing
- **pre-commit** for Git hooks

All code must:

- Pass all linting checks (`uv run task lint`)
- Be properly typed (checked by mypy)
- Be formatted with Ruff (`uv run task format`)
- Include appropriate tests

## Environment Variables

See the [Configuration Guide](../operations/configuration.md) for detailed environment variable
documentation.

### Development Defaults

For local development, you can create a `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://apollonia:apollonia@localhost:5432/apollonia
POSTGRES_USER=apollonia
POSTGRES_PASSWORD=apollonia
POSTGRES_DB=apollonia

# AMQP Configuration
AMQP_CONNECTION_STRING=amqp://apollonia:apollonia@localhost:5672/
RABBITMQ_DEFAULT_USER=apollonia
RABBITMQ_DEFAULT_PASS=apollonia

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=apollonia
NEO4J_AUTH=neo4j/apollonia

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
JWT_SECRET_KEY=your-secret-key-here
API_BASE_URL=http://localhost:8000

# Ingestor Configuration
DATA_DIRECTORY=./data

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```

## Debugging

### Running with Logging

Both services use Python's standard logging. To increase verbosity:

```python
# Set in your environment
export PYTHONUNBUFFERED=1
export LOG_LEVEL=DEBUG
```

### Debugging in VS Code

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Ingestor",
            "type": "python",
            "request": "launch",
            "module": "ingestor.ingestor",
            "env": {
                "AMQP_CONNECTION_STRING": "amqp://apollonia:apollonia@localhost:5672/",
                "DATA_DIRECTORY": "${workspaceFolder}/data"
            }
        },
        {
            "name": "Populator",
            "type": "python",
            "request": "launch",
            "module": "populator.populator",
            "env": {
                "AMQP_CONNECTION_STRING": "amqp://apollonia:apollonia@localhost:5672/",
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "apollonia"
            }
        }
    ]
}
```

## Contributing

1. Create a feature branch from `main`
1. Make your changes following the code standards
1. Ensure all tests pass and add new tests for new functionality
1. Run `uv run task check-all` before committing
1. Submit a pull request with a clear description

## Troubleshooting

### Common Issues

**Issue**: Pre-commit hooks failing

```bash
# Update hooks to latest versions
uv run task update-hooks

# Run manually to see specific errors
uv run task check-all
```

**Issue**: Docker build failing

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Issue**: Services can't connect to RabbitMQ/Neo4j

```bash
# Check services are running
docker-compose ps

# Check logs
docker-compose logs rabbitmq
docker-compose logs neo4j

# Ensure services are healthy
docker-compose ps | grep healthy
```

## Next Steps

- Review the [Architecture Overview](../architecture/overview.md)
- Check service-specific documentation:
  - [Ingestor Service](../services/ingestor.md) - File monitoring and detection
  - [Analyzer Service](../services/analyzer.md) - ML-powered media analysis
  - [Populator Service](../services/populator.md) - Database persistence
  - [API Service](../services/api.md) - REST and GraphQL endpoints
- Review additional guides:
  - [Testing Guide](testing.md) - Unit, integration, and E2E testing
  - [Justfile Guide](justfile-guide.md) - Task runner commands
  - [Logging Convention](logging-convention.md) - Emoji-based logging
  - [GitHub Workflows](github-workflows.md) - CI/CD pipelines
