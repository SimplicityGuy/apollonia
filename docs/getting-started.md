# Getting Started with Apollonia

Welcome to Apollonia! This guide will help you get up and running with the media catalog system
quickly.

## Overview

Apollonia is a comprehensive media catalog system that automatically detects, classifies, and
analyzes audio and video files using machine learning. This guide covers the essential steps to get
started.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker & Docker Compose** (recommended for quick start)
- **Python 3.12+** (for local development)
- **Node.js 18+** (for frontend development)
- **Git** (for version control)

### System Requirements

- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **OS**: Linux, macOS, or Windows with WSL2

## Quick Start (Docker)

The fastest way to get Apollonia running is with Docker Compose:

### 1. Clone the Repository

```bash
git clone https://github.com/SimplicityGuy/apollonia.git
cd apollonia
```

### 2. Start All Services

```bash
# Start all services in the background
docker-compose up -d

# Monitor the logs
docker-compose logs -f
```

### 3. Verify Services

Wait for all services to start (usually 1-2 minutes), then check:

```bash
# Check service status
docker-compose ps

# Verify services are healthy
docker-compose exec rabbitmq rabbitmq-diagnostics ping
docker-compose exec postgres pg_isready -U apollonia
```

### 4. Access the Web Interface

Open your browser and navigate to:

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### 5. Upload Your First Media Files

**Option A: Web Interface**

1. Click "Upload" in the web interface
1. Select your media files
1. Watch them being processed in real-time

**Option B: Directory Monitoring**

```bash
# Copy files to the monitored directory
mkdir -p ./data/music ./data/videos
cp /path/to/your/music/* ./data/music/
cp /path/to/your/videos/* ./data/videos/
```

## Development Setup

For local development with full control:

### 1. Install Just (Task Runner)

```bash
# On macOS
brew install just

# On Linux/WSL
cargo install just

# Or download from https://just.systems/
```

### 2. Development Environment Setup

```bash
# Complete development setup
just install

# This runs:
# - uv sync --all-extras (Python dependencies)
# - npm ci (Frontend dependencies)
# - pre-commit install (Git hooks)
# - Docker service setup
```

### 3. Start Development Services

```bash
# Start infrastructure services only
just up-infra

# Start all services for development
just up

# Start services individually
just ingestor    # File monitoring service
just populator   # Database population service
just api         # REST/GraphQL API
just frontend    # React web application
```

### 4. Development Workflow

```bash
# Run quality checks
just check

# Run tests
just test

# Build everything
just build

# See all available commands
just --list
```

## Configuration

### Environment Variables

Create a `.env` file in the project root for custom configuration:

```bash
# Database Configuration
POSTGRES_USER=apollonia
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=apollonia

# RabbitMQ Configuration
RABBITMQ_DEFAULT_USER=apollonia
RABBITMQ_DEFAULT_PASS=your_secure_password

# Neo4j Configuration (optional)
NEO4J_AUTH=neo4j/your_secure_password

# API Configuration
JWT_SECRET_KEY=your_jwt_secret
API_BASE_URL=http://localhost:8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
```

### Media Directories

Configure the directories that Apollonia monitors:

```bash
# Default monitored directories
./data/
├── music/          # Audio files
├── videos/         # Video files
├── podcasts/       # Podcast episodes
└── audiobooks/     # Audiobook files
```

## Supported Media Formats

### Audio Formats

- MP3, WAV, FLAC, OGG, AAC
- Sample rates: 8kHz to 192kHz
- Bit depths: 16-bit, 24-bit, 32-bit

### Video Formats

- MP4, AVI, MOV, WMV, MKV
- Codecs: H.264, H.265, VP9, AV1
- Resolutions: 480p to 4K+

## Basic Usage

### Web Interface

1. **Dashboard**: Overview of your media collection
1. **Browse**: Explore by genre, artist, album, or custom tags
1. **Search**: Full-text search across metadata and content
1. **Analytics**: Insights about your collection
1. **Upload**: Add new media files

### API Usage

```bash
# Get collection overview
curl http://localhost:8000/api/v1/stats

# Search for media
curl "http://localhost:8000/api/v1/search?q=classical"

# Get media details
curl http://localhost:8000/api/v1/media/123
```

### GraphQL Interface

```graphql
query GetMedia($limit: Int = 10) {
  media(limit: $limit) {
    id
    title
    artist
    genre
    duration
    audioFeatures {
      tempo
      key
      energy
    }
  }
}
```

## Troubleshooting

### Common Issues

**Services won't start:**

```bash
# Check Docker resources
docker system df
docker system prune  # If low on space

# Check port conflicts
netstat -tlnp | grep :3000
netstat -tlnp | grep :8000
```

**Database connection errors:**

```bash
# Reset database
docker-compose down -v
docker-compose up postgres -d
# Wait 30 seconds, then start other services
```

**File processing not working:**

```bash
# Check ingestor logs
docker-compose logs ingestor

# Verify RabbitMQ connectivity
docker-compose exec ingestor python -c "import pika; print('OK')"
```

### Getting Help

- **Documentation**: Browse the [full documentation](../README.md)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/SimplicityGuy/apollonia/issues)
- **Development**: See [Contributing Guide](../CONTRIBUTING.md)

### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ingestor
docker-compose logs -f api

# Enable debug mode
export APOLLONIA_LOG_LEVEL=DEBUG
docker-compose up
```

## Next Steps

Now that you have Apollonia running:

1. **Explore the Interface**: Navigate through the web application
1. **Add Your Media**: Upload or copy files to monitored directories
1. **Check Analytics**: View insights about your collection
1. **Customize Settings**: Adjust configuration for your needs
1. **API Integration**: Integrate with other tools using the API

For more advanced usage, see:

- [Development Guide](development/development-guide.md)
- [API Documentation](api/README.md)
- [Architecture Overview](architecture/overview.md)

## Performance Tips

- **SSD Storage**: Use SSD storage for better I/O performance
- **Memory**: Allocate sufficient RAM for ML processing
- **Network**: Use gigabit networking for large file transfers
- **Indexing**: Allow time for initial indexing of large collections

Welcome to Apollonia! 🎵📹
