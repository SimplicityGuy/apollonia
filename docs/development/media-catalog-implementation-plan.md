# Media Catalog Implementation Plan

## Executive Summary

This document outlines a comprehensive plan for building an advanced media cataloging system that
combines file monitoring, ML-based audio analysis, and a rich frontend interface. The system will
leverage the existing Apollonia microservices architecture and incorporate ML models from the
catalogger research project.

## Project Goals

1. **Automated Media Discovery**: Monitor directories for music and video files
1. **ML-Powered Analysis**: Extract genres, moods, attributes, and other metadata using pre-trained
   models
1. **Rich Metadata Storage**: Store file information and ML predictions in a graph database
1. **Intuitive Frontend**: Provide a web interface for browsing, searching, and managing media
1. **Scalable Architecture**: Handle large media collections efficiently

## System Architecture

### Core Components

1. **File Monitoring Service** (Based on Apollonia Ingestor)

   - Monitor multiple directories for media files
   - Compute file hashes (SHA256, xxh128)
   - Detect media file types (audio/video)
   - Publish file events to message queue

1. **ML Analysis Service** (New)

   - Consume file events from queue
   - Apply ML models for audio analysis:
     - Genre classification (Discogs EffNet)
     - Mood detection (acoustic, electronic, happy, sad, etc.)
     - Music attributes (danceability, gender, tonality, voice/instrumental)
   - Extract traditional metadata (ID3 tags, duration, bitrate)
   - Publish enriched metadata to queue

1. **Database Populator** (Enhanced Apollonia Populator)

   - Consume enriched metadata from queue
   - Store in Neo4j graph database with relationships:
     - Files → Artists → Albums → Genres
     - Files → Moods → Playlists
     - Files → Attributes → Recommendations

1. **API Service** (New)

   - GraphQL/REST API for frontend
   - Query capabilities:
     - Search by genre, mood, artist, etc.
     - Get recommendations based on attributes
     - Playlist generation
   - File streaming endpoints

1. **Frontend Application** (New)

   - Modern React/Vue.js application
   - Features:
     - Media library browsing
     - Advanced search and filtering
     - Visualization of ML predictions
     - Playlist management
     - Media player integration

### Technology Stack

- **Backend**: Python 3.12
- **ML Framework**: TensorFlow + Essentia
- **Message Queue**: RabbitMQ (AMQP)
- **Database**: Neo4j (graph) + PostgreSQL (optional for specific data)
- **API**: FastAPI with GraphQL support
- **Frontend**: React with TypeScript
- **Container**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

1. **Extend Apollonia Ingestor**

   - Add media file type detection
   - Support for multiple watch directories
   - Enhanced file metadata extraction

1. **Create ML Analysis Service**

   - Set up service skeleton based on Apollonia patterns
   - Integrate Essentia and TensorFlow
   - Implement model loading and caching
   - Create analysis pipeline for single files

1. **Enhance Database Schema**

   - Design Neo4j schema for media catalog
   - Create nodes: File, Artist, Album, Genre, Mood, Attribute
   - Define relationships and indices

### Phase 2: ML Integration (Weeks 3-4)

1. **Implement ML Pipelines**

   - Genre prediction (Discogs model)
   - Mood classification (6 mood types)
   - Music attributes (danceability, tonality, etc.)
   - Batch processing optimization

1. **Model Management**

   - Download and cache ML models
   - Version management
   - Performance optimization (GPU support)

1. **Testing and Validation**

   - Unit tests for ML predictions
   - Integration tests with sample media
   - Performance benchmarking

### Phase 3: API Development (Weeks 5-6)

1. **Design API Schema**

   - GraphQL schema definition
   - REST endpoints for streaming
   - Authentication and authorization

1. **Implement API Service**

   - FastAPI application setup
   - Neo4j query optimization
   - Caching layer (Redis)
   - Rate limiting and security

1. **API Documentation**

   - OpenAPI/Swagger docs
   - GraphQL playground
   - Usage examples

### Phase 4: Frontend Development (Weeks 7-9)

1. **UI/UX Design**

   - Wireframes and mockups
   - Component library selection
   - Responsive design

1. **Core Features**

   - Media library grid/list views
   - Search and filter interface
   - ML prediction visualizations
   - Media player integration

1. **Advanced Features**

   - Playlist management
   - Recommendation engine UI
   - Batch operations
   - User preferences

### Phase 5: Integration & Polish (Weeks 10-11)

1. **End-to-End Testing**

   - Full workflow testing
   - Performance optimization
   - Error handling

1. **Deployment**

   - Docker Compose configuration
   - CI/CD pipeline
   - Monitoring setup

1. **Documentation**

   - User guide
   - Developer documentation
   - Deployment guide

### Phase 6: Advanced Features (Weeks 12+)

1. **Video Support**

   - Video file analysis
   - Thumbnail generation
   - Scene detection

1. **Advanced ML Features**

   - Custom model training
   - User preference learning
   - Similarity search

1. **Social Features**

   - Sharing capabilities
   - Collaborative playlists
   - Import/export

## Data Flow

```
Media Files
    ↓
[Ingestor Service]
    ↓ (file metadata)
AMQP Queue
    ↓
[ML Analysis Service]
    ↓ (enriched metadata)
AMQP Queue
    ↓
[Populator Service]
    ↓
Neo4j Database
    ↓
[API Service]
    ↓
[Frontend App]
```

## ML Model Integration Details

### Models from Catalogger Research

1. **Genre Classification**

   - Model: `discogs-effnet-bs64-1`
   - Input: Audio file
   - Output: Top 5 genres with confidence scores

1. **Mood Prediction**

   - Models: MusiCNN MSD/MTT + VGGish
   - Categories: acoustic, electronic, aggressive, relaxed, happy, sad, party
   - Output: Probability scores for each mood

1. **Music Attributes**

   - Danceability score
   - Gender prediction (male/female vocals)
   - Tonality (tonal/atonal)
   - Voice/Instrumental classification

### Model Deployment Strategy

1. **Model Storage**

   - Store models in object storage (S3/MinIO)
   - Version control for model updates
   - Lazy loading to optimize memory

1. **Processing Pipeline**

   - Queue-based processing for scalability
   - Batch processing for efficiency
   - GPU acceleration where available

1. **Result Caching**

   - Cache predictions in database
   - Invalidate on file changes
   - Background reprocessing

## Database Schema Design

### Neo4j Nodes

```cypher
// File Node
(:File {
  id: UUID,
  sha256: String,
  xxh128: String,
  path: String,
  filename: String,
  size: Integer,
  created: DateTime,
  modified: DateTime,
  duration: Float,
  bitrate: Integer,
  format: String
})

// Artist Node
(:Artist {
  id: UUID,
  name: String,
  musicbrainz_id: String
})

// Album Node
(:Album {
  id: UUID,
  name: String,
  year: Integer,
  musicbrainz_id: String
})

// Genre Node
(:Genre {
  id: UUID,
  name: String,
  parent: String
})

// Mood Node
(:Mood {
  id: UUID,
  type: String,
  confidence: Float
})

// Attribute Node
(:Attribute {
  id: UUID,
  type: String,
  value: Float,
  model: String
})
```

### Relationships

```cypher
(file:File)-[:PERFORMED_BY]->(artist:Artist)
(file:File)-[:APPEARS_ON]->(album:Album)
(file:File)-[:HAS_GENRE {confidence: Float}]->(genre:Genre)
(file:File)-[:HAS_MOOD {confidence: Float}]->(mood:Mood)
(file:File)-[:HAS_ATTRIBUTE]->(attribute:Attribute)
(album:Album)-[:BY_ARTIST]->(artist:Artist)
```

## API Endpoints Design

### GraphQL Schema

```graphql
type File {
  id: ID!
  filename: String!
  path: String!
  duration: Float
  genres: [Genre!]!
  moods: [Mood!]!
  attributes: [Attribute!]!
  artist: Artist
  album: Album
}

type Query {
  files(filter: FileFilter, limit: Int, offset: Int): [File!]!
  file(id: ID!): File
  search(query: String!): SearchResult!
  recommendations(fileId: ID!, limit: Int): [File!]!
}

input FileFilter {
  genres: [String!]
  moods: [String!]
  minDanceability: Float
  maxDanceability: Float
  vocal: Boolean
}
```

### REST Endpoints

```
GET /api/v1/files
GET /api/v1/files/{id}
GET /api/v1/files/{id}/stream
GET /api/v1/search?q={query}
GET /api/v1/genres
GET /api/v1/moods
POST /api/v1/playlists
GET /api/v1/recommendations/{id}
```

## Development Environment Setup

### Prerequisites

```bash
# System requirements
- Python 3.12
- Docker & Docker Compose
- Node.js 18+
- CUDA toolkit (optional, for GPU acceleration)

# ML Models (will be downloaded automatically)
- Discogs EffNet genre model
- MusiCNN mood models
- VGGish attribute models
```

### Initial Setup

```bash
# Clone repositories
git clone https://github.com/SimplicityGuy/apollonia.git
cd apollonia

# Create ml-models directory
mkdir -p ml-models

# Set up Python environment
uv sync --all-extras

# Install pre-commit hooks
uv run task install-hooks

# Start infrastructure
docker-compose up -d rabbitmq neo4j

# Create database schema
docker exec -it apollonia-neo4j cypher-shell < schema.cypher
```

## Testing Strategy

### Unit Tests

- ML model predictions
- File processing logic
- API endpoints
- Database operations

### Integration Tests

- End-to-end file processing
- ML pipeline performance
- API response times
- Frontend interactions

### Performance Tests

- Large file processing
- Concurrent analysis
- Database query optimization
- API load testing

## Monitoring & Observability

### Metrics

- File processing rate
- ML prediction latency
- Queue depths
- API response times
- Error rates

### Logging

- Structured logging (JSON)
- Correlation IDs
- Log aggregation (ELK stack)

### Alerts

- Queue backlog
- Processing failures
- Model errors
- API availability

## Security Considerations

1. **Authentication**

   - JWT tokens for API
   - User management
   - Role-based access

1. **Data Protection**

   - Encrypted file storage
   - Secure API endpoints
   - Input validation

1. **Privacy**

   - User data isolation
   - GDPR compliance
   - Data retention policies

## Future Enhancements

1. **Advanced ML Features**

   - BPM detection
   - Key detection
   - Audio fingerprinting
   - Duplicate detection

1. **Streaming Integration**

   - Spotify/Apple Music metadata
   - Last.fm scrobbling
   - MusicBrainz integration

1. **Mobile Applications**

   - iOS/Android apps
   - Offline support
   - Sync capabilities

1. **Cloud Deployment**

   - Kubernetes manifests
   - Auto-scaling
   - Multi-region support

## Success Metrics

1. **Performance**

   - Process 1000 files/hour
   - < 5s per file ML analysis
   - < 100ms API response time

1. **Accuracy**

   - > 80% genre prediction accuracy
   - > 75% mood classification accuracy
   - < 5% processing failures

1. **User Experience**

   - < 2s page load time
   - Intuitive navigation
   - Rich visualizations

## Next Steps

1. Review and approve this implementation plan
1. Set up development environment
1. Begin Phase 1 implementation
1. Weekly progress reviews
1. Adjust timeline based on discoveries

______________________________________________________________________

This plan is a living document and will be updated as the project progresses. Each phase will have
detailed technical specifications and acceptance criteria defined before implementation begins.
