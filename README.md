# apollonia

![apollonia](https://github.com/SimplicityGuy/apollonia/actions/workflows/build.yml/badge.svg)
![License: MIT](https://img.shields.io/github/license/SimplicityGuy/apollonia)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Pronunciation: _a·pol·lon·ia_

## Overview

Apollonia is a Python-based microservices architecture for file monitoring and processing, using
AMQP message queuing for service communication. The system monitors directories for new files,
extracts metadata, and stores the information in a Neo4j graph database.

## Architecture

The project consists of two main services:

- **[Ingestor](docs/services/ingestor.md)**: Monitors directories for new files and publishes
  metadata to AMQP
- **[Populator](docs/services/populator.md)**: Consumes messages from AMQP and imports data to Neo4j

## Requirements

- Python 3.13+ (primary target)
- Python 3.12 is tested for compatibility in CI/CD
- Docker and Docker Compose for containerized deployment
- RabbitMQ for message queuing
- Neo4j for graph database storage

## Quick Start

1. **Clone the repository**:

   ```bash
   git clone https://github.com/SimplicityGuy/apollonia.git
   cd apollonia
   ```

1. **Start the services**:

   ```bash
   docker-compose up -d
   ```

1. **Monitor the logs**:

   ```bash
   docker-compose logs -f
   ```

1. **Add files to monitor**:

   ```bash
   cp your-files/* ./data/
   ```

## Development

For detailed development instructions, see the
[Development Guide](docs/development/development-guide.md).

### Quick Development Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run task install-hooks

# Run quality checks
uv run task check
```

## Documentation

- **Development**

  - [Development Guide](docs/development/development-guide.md) - Setup and workflow instructions
  - [Python Version Notes](docs/development/python-version-notes.md) - Python version strategy
  - [Roadmap](docs/development/roadmap.md) - Future development phases
  - [Architecture Overview](docs/architecture/overview.md) - System design and components

- **Services**

  - [Ingestor Service](docs/services/ingestor.md) - File monitoring service details
  - [Populator Service](docs/services/populator.md) - Neo4j import service details

- **Operations**

  - [Docker Deployment](docs/operations/docker-deployment.md) - Container deployment guide
  - [Configuration](docs/operations/configuration.md) - Environment variables and settings

- **Contributing**

  - [Claude Code Guide](CLAUDE.md) - Instructions for AI-assisted development

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Robert Wlodarczyk - [robert@simplicityguy.com](mailto:robert@simplicityguy.com)
