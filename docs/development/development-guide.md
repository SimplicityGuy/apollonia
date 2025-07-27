# Development Guide

This guide covers the development setup and workflow for the Apollonia project.

## Prerequisites

- Python 3.12
- Docker and Docker Compose
- uv package manager
- Git

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
# Start dependencies (RabbitMQ and Neo4j)
docker-compose up -d rabbitmq neo4j

# Run the ingestor service
uv run task ingestor

# Run the populator service (in another terminal)
uv run task populator
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
│   ├── __init__.py
│   ├── ingestor.py       # Main service entry point
│   ├── prospector.py     # File metadata extraction
│   ├── pyproject.toml    # Package configuration
│   └── Dockerfile
├── populator/            # Neo4j import service
│   ├── __init__.py
│   ├── populator.py      # Main service entry point
│   ├── pyproject.toml    # Package configuration
│   └── Dockerfile
├── tests/                # Test suite
│   ├── ingestor/
│   └── populator/
├── docs/                 # Documentation
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
# AMQP Configuration
AMQP_CONNECTION_STRING=amqp://apollonia:apollonia@localhost:5672/

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=apollonia

# Ingestor Configuration
DATA_DIRECTORY=./data
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
  - [Ingestor Service](../services/ingestor.md)
  - [Populator Service](../services/populator.md)
