# apollonia

![apollonia](https://github.com/SimplicityGuy/apollonia/actions/workflows/build.yml/badge.svg)
![License: MIT](https://img.shields.io/github/license/SimplicityGuy/apollonia)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Pronunciation: _a·pol·lon·ia_

## Overview

Apollonia is a comprehensive media catalog system that automatically detects, classifies, and
analyzes audio and video files using machine learning. Built with a modern microservices
architecture, it provides real-time processing, advanced analytics, and a responsive web interface
for managing large media collections.

## Key Features

- **Automatic Media Detection**: Monitors directories and automatically processes new media files
- **ML-Powered Analysis**: Uses TensorFlow and Essentia for audio/video feature extraction
- **Real-time Processing**: Event-driven architecture with AMQP message queuing
- **Comprehensive API**: RESTful and GraphQL APIs with JWT authentication
- **Modern Web Interface**: React-based UI with real-time updates and analytics
- **Scalable Architecture**: Microservices design with Docker containerization
- **Multi-format Support**: Handles various audio (MP3, WAV, FLAC) and video (MP4, AVI, MOV) formats

## Architecture

The system consists of several specialized services:

- **[Media Ingestor](docs/services/ingestor.md)**: Monitors directories and detects media files
- **[ML Analyzer](docs/services/analyzer.md)**: Extracts features using TensorFlow/Essentia models
- **[Database Populator](docs/services/populator.md)**: Stores metadata in PostgreSQL and Neo4j
- **[API Service](docs/services/api.md)**: Provides REST and GraphQL endpoints
- **[Frontend](frontend/README.md)**: React-based web application

## Requirements

- Python 3.12 (for TensorFlow/Essentia compatibility)
- Docker and Docker Compose for containerized deployment
- PostgreSQL for primary data storage
- RabbitMQ for message queuing
- Redis for caching
- Neo4j for graph relationships (optional)
- Node.js 18+ for frontend development

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

1. **Access the web interface**:

   Open http://localhost:3000 in your browser

   Default credentials:

   - Username: admin
   - Password: admin123

1. **Add media files**:

   ```bash
   # Copy files to monitored directories
   cp your-music/* ./data/music/
   cp your-videos/* ./data/videos/

   # Or use the web interface upload feature
   ```

## Development

For detailed development instructions, see the
[Development Guide](docs/development/development-guide.md).

### Quick Development Setup

The project uses [Just](https://just.systems/) as a command runner for all development tasks.

```bash
# Install Just (if not already installed)
cargo install just

# Or on macOS
brew install just

# Set up development environment
just install

# Start all services
just up

# Run tests
just test

# Run quality checks
just check

# See all available commands
just --list
```

### Alternative Setup (without Just)

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

- **Getting Started**

  - [Quick Start Guide](docs/getting-started.md) - Initial setup and usage
  - [Architecture Overview](docs/architecture/overview.md) - System design and components
  - [API Documentation](docs/api/README.md) - REST and GraphQL reference

- **Development**

  - [Development Guide](docs/development/development-guide.md) - Setup and workflow instructions
  - [Python Version Notes](docs/development/python-version-notes.md) - Python version strategy
  - [Frontend Development](frontend/README.md) - React application guide
  - [Testing Guide](docs/development/testing.md) - Unit, integration, and E2E tests

- **Services**

  - [Media Ingestor](docs/services/ingestor.md) - File monitoring service
  - [ML Analyzer](docs/services/analyzer.md) - Machine learning analysis
  - [Database Populator](docs/services/populator.md) - Data persistence service
  - [API Service](docs/services/api.md) - REST and GraphQL endpoints

- **Operations**

  - [Docker Deployment](docs/operations/docker-deployment.md) - Container deployment guide
  - [Configuration](docs/operations/configuration.md) - Environment variables and settings
  - [Performance Tuning](docs/operations/performance.md) - Optimization guide
  - [Monitoring](docs/operations/monitoring.md) - Metrics and observability

- **CI/CD**

  - [GitHub Workflows](docs/development/github-workflows.md) - CI/CD pipeline documentation
  - [Emoji Logging Convention](docs/development/logging-convention.md) - Standardized logging with
    emojis
  - [Justfile Commands](docs/development/justfile-guide.md) - Development task runner reference

- **Contributing**

  - [Contributing Guide](CONTRIBUTING.md) - How to contribute
  - [Claude Code Guide](CLAUDE.md) - Instructions for AI-assisted development

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Robert Wlodarczyk - [robert@simplicityguy.com](mailto:robert@simplicityguy.com)
