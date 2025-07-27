# apollonia

## 🚀 CI/CD Status

[![CI/CD Pipeline](https://github.com/SimplicityGuy/apollonia/actions/workflows/build.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/build.yml)
[![Quality Checks](https://github.com/SimplicityGuy/apollonia/actions/workflows/quality.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/quality.yml)
[![Tests](https://github.com/SimplicityGuy/apollonia/actions/workflows/test.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/test.yml)
[![Docker Build & Deploy](https://github.com/SimplicityGuy/apollonia/actions/workflows/docker.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/docker.yml)
[![Deploy](https://github.com/SimplicityGuy/apollonia/actions/workflows/deploy.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/deploy.yml)
[![Dependencies](https://github.com/SimplicityGuy/apollonia/actions/workflows/dependencies.yml/badge.svg)](https://github.com/SimplicityGuy/apollonia/actions/workflows/dependencies.yml)

## 📦 Project Info

![License: MIT](https://img.shields.io/github/license/SimplicityGuy/apollonia)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg?logo=docker)](https://www.docker.com/)

## 🛠️ Code Quality

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-enabled-blue.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## 🧪 Testing & Security

[![pytest](https://img.shields.io/badge/pytest-enabled-blue.svg?logo=pytest)](https://docs.pytest.org/)
[![Vitest](https://img.shields.io/badge/vitest-enabled-green.svg?logo=vitest)](https://vitest.dev/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://bandit.readthedocs.io/)
[![Dependencies: pip-audit](https://img.shields.io/badge/dependencies-pip--audit-blue.svg)](https://pypi.org/project/pip-audit/)
[![Containers: Trivy](https://img.shields.io/badge/containers-trivy-blue.svg)](https://trivy.dev/)

## 📊 Project Metrics

[![GitHub issues](https://img.shields.io/github/issues/SimplicityGuy/apollonia)](https://github.com/SimplicityGuy/apollonia/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/SimplicityGuy/apollonia)](https://github.com/SimplicityGuy/apollonia/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/SimplicityGuy/apollonia)](https://github.com/SimplicityGuy/apollonia/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/SimplicityGuy/apollonia)](https://github.com/SimplicityGuy/apollonia)
[![Lines of code](https://img.shields.io/tokei/lines/github/SimplicityGuy/apollonia)](https://github.com/SimplicityGuy/apollonia)

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

## 🛠️ Technologies & Tools

### Core Technologies

- **Backend**: [Python 3.12](https://www.python.org/) | [FastAPI](https://fastapi.tiangolo.com/) |
  [Strawberry GraphQL](https://strawberry.rocks/)
- **Frontend**: [React 18](https://react.dev/) | [TypeScript](https://www.typescriptlang.org/) |
  [Vite](https://vitejs.dev/) | [Tailwind CSS](https://tailwindcss.com/)
- **Machine Learning**: [TensorFlow](https://www.tensorflow.org/) |
  [Essentia](https://essentia.upf.edu/) | [Librosa](https://librosa.org/)
- **Databases**: [PostgreSQL](https://www.postgresql.org/) | [Neo4j](https://neo4j.com/) |
  [Redis](https://redis.io/)
- **Message Queue**: [RabbitMQ](https://www.rabbitmq.com/) |
  [aio-pika](https://aio-pika.readthedocs.io/)

### Development Tools

- **Package Management**: [uv](https://github.com/astral-sh/uv) | [npm](https://www.npmjs.com/)
- **Task Runner**: [Just](https://just.systems/) | [Taskipy](https://github.com/illBeRoy/taskipy)
- **Code Quality**: [Ruff](https://docs.astral.sh/ruff/) | [mypy](http://mypy-lang.org/) |
  [ESLint](https://eslint.org/) | [Prettier](https://prettier.io/)
- **Testing**: [pytest](https://docs.pytest.org/) | [Vitest](https://vitest.dev/) |
  [Testing Library](https://testing-library.com/)
- **Git Hooks**: [pre-commit](https://pre-commit.com/)

### Infrastructure & DevOps

- **Containerization**: [Docker](https://www.docker.com/) |
  [Docker Compose](https://docs.docker.com/compose/)
- **CI/CD**: [GitHub Actions](https://github.com/features/actions)
- **Container Registry**:
  [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- **Monitoring**: [Prometheus](https://prometheus.io/) | [Grafana](https://grafana.com/) |
  [Jaeger](https://www.jaegertracing.io/)

### Frontend Libraries

- **UI Components**: [Radix UI](https://www.radix-ui.com/) | [Headless UI](https://headlessui.com/)
  | [Heroicons](https://heroicons.com/)
- **State Management**: [Zustand](https://github.com/pmndrs/zustand) |
  [TanStack Query](https://tanstack.com/query/)
- **Data Visualization**: [Recharts](https://recharts.org/) |
  [Framer Motion](https://www.framer.com/motion/)
- **Forms**: [React Hook Form](https://react-hook-form.com/) | [Zod](https://zod.dev/)

### Media Processing

- **Audio Analysis**: [xxhash](https://github.com/Cyan4973/xxHash) | [NumPy](https://numpy.org/) |
  [MoviePy](https://zulko.github.io/moviepy/)
- **File Monitoring**: [asyncinotify](https://github.com/absperf/asyncinotify)
- **Data Serialization**: [orjson](https://github.com/ijl/orjson)

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

### Development Tools Overview

- **🚀 Package Manager**: [uv](https://github.com/astral-sh/uv) - Ultra-fast Python package installer
  and resolver
- **🎯 Task Runner**: [Just](https://just.systems/) - Command runner for development workflows
- **🧹 Code Formatter**: [Ruff](https://docs.astral.sh/ruff/) - Extremely fast Python linter and
  formatter
- **🔍 Type Checker**: [mypy](http://mypy-lang.org/) - Static type checker for Python
- **🧪 Testing**: [pytest](https://docs.pytest.org/) for Python | [Vitest](https://vitest.dev/) for
  Frontend
- **🛡️ Security**: [Bandit](https://bandit.readthedocs.io/) |
  [pip-audit](https://pypi.org/project/pip-audit/) | [Trivy](https://trivy.dev/)
- **🪝 Git Hooks**: [pre-commit](https://pre-commit.com/) - Multi-language pre-commit framework
- **📦 Containerization**: [Docker](https://www.docker.com/) with multi-stage builds and health
  checks

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
