# API Documentation

Apollonia provides REST and GraphQL APIs for programmatic access to the intelligent media catalog
system. The API enables file management, ML-powered analysis retrieval, and real-time processing
updates.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [REST API](#rest-api)
- [GraphQL API](#graphql-api)
- [WebSocket API](#websocket-api)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [SDK and Examples](#sdk-and-examples)

## Overview

The Apollonia API offers multiple interfaces for different use cases:

- **REST API**: Standard HTTP endpoints for CRUD operations on media files
- **GraphQL API**: Flexible query interface for complex data retrieval and relationships
- **WebSocket API**: Real-time updates for file processing and ML analysis
- **Admin API**: Administrative functions and system management

### Base URLs

- **Production**: `https://api.apollonia.example.com`
- **Development**: `http://localhost:8000`
- **GraphQL Endpoint**: `/graphql`
- **REST API Base**: `/api/v1`
- **WebSocket**: `/ws`

### Current Implementation Status

- ✅ **FastAPI Service**: RESTful API with automatic OpenAPI documentation
- ✅ **GraphQL with Strawberry**: Type-safe GraphQL schema and resolvers
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **File Upload**: Multipart form uploads with metadata
- ✅ **Real-time Updates**: WebSocket support for processing status
- 🚧 **ML Feature Endpoints**: Audio/video analysis results (in progress)
- 🚧 **Search API**: Full-text and similarity search (planned)

## Authentication

Apollonia uses JWT (JSON Web Tokens) for authentication.

### Obtaining a Token

```bash
# Login with credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/media
```

### Token Refresh

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## REST API

### Media Endpoints

#### List Media

```http
GET /api/v1/media
```

**Query Parameters:**

- `limit` (int): Number of results (default: 50, max: 500)
- `offset` (int): Pagination offset (default: 0)
- `genre` (string): Filter by genre
- `artist` (string): Filter by artist
- `format` (string): Filter by file format
- `sort` (string): Sort field (title, artist, created_at, duration)
- `order` (string): Sort order (asc, desc)

**Example:**

```bash
curl "http://localhost:8000/api/v1/media?limit=10&genre=jazz&sort=title"
```

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Blue Train",
      "artist": "John Coltrane",
      "album": "Blue Train",
      "genre": "Jazz",
      "duration": 642,
      "file_path": "/data/music/blue_train.flac",
      "format": "flac",
      "created_at": "2024-01-01T12:00:00Z",
      "audio_features": {
        "tempo": 120.5,
        "key": "C",
        "energy": 0.75,
        "valence": 0.85
      }
    }
  ],
  "total": 1250,
  "limit": 10,
  "offset": 0
}
```

#### Get Media Details

```http
GET /api/v1/media/{id}
```

**Response:**

```json
{
  "id": "uuid",
  "title": "Blue Train",
  "artist": "John Coltrane",
  "album": "Blue Train",
  "genre": "Jazz",
  "duration": 642,
  "file_path": "/data/music/blue_train.flac",
  "format": "flac",
  "file_size": 45728394,
  "bit_rate": 1411,
  "sample_rate": 44100,
  "channels": 2,
  "sha256_hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
  "xxh128_hash": "a94a8fe5ccb19ba61c4c",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "audio_features": {
    "tempo": 120.5,
    "key": "C",
    "mode": "major",
    "time_signature": 4,
    "energy": 0.75,
    "valence": 0.85,
    "acousticness": 0.65,
    "instrumentalness": 0.92,
    "liveness": 0.15,
    "speechiness": 0.04
  },
  "technical_analysis": {
    "spectral_centroid": 2156.8,
    "spectral_rolloff": 8420.1,
    "zero_crossing_rate": 0.078,
    "mfcc": [1.2, -0.8, 0.5, ...]
  },
  "tags": ["jazz", "classic", "instrumental"],
  "neighbors": [
    {
      "id": "neighbor_uuid",
      "path": "/data/music/a_love_supreme.flac",
      "relationship": "NEIGHBOR"
    }
  ]
}
```

#### Search Media

```http
GET /api/v1/search
```

**Query Parameters:**

- `q` (string, required): Search query
- `fields` (array): Fields to search (title, artist, album, genre, tags)
- `limit` (int): Number of results
- `offset` (int): Pagination offset
- `filters` (object): Additional filters

**Example:**

```bash
curl "http://localhost:8000/api/v1/search?q=jazz%20piano&fields=title,artist,genre"
```

#### Upload Media

```http
POST /api/v1/media/upload
```

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/media/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@song.mp3" \
  -F "metadata={\"title\":\"Song Title\",\"artist\":\"Artist Name\"}"
```

### Collection Endpoints

#### Get Collections

```http
GET /api/v1/collections
```

#### Create Collection

```http
POST /api/v1/collections
```

**Request Body:**

```json
{
  "name": "My Jazz Collection",
  "description": "Favorite jazz tracks",
  "is_public": false,
  "media_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Analytics Endpoints

#### Collection Statistics

```http
GET /api/v1/stats
```

**Response:**

```json
{
  "total_media": 5420,
  "total_duration": 1234567,
  "total_size": 987654321,
  "genres": {
    "jazz": 1200,
    "rock": 980,
    "classical": 750
  },
  "formats": {
    "flac": 2100,
    "mp3": 2890,
    "wav": 430
  },
  "upload_trend": [
    {"date": "2024-01-01", "count": 25},
    {"date": "2024-01-02", "count": 30}
  ]
}
```

#### Audio Feature Analysis

```http
GET /api/v1/analytics/features
```

**Query Parameters:**

- `feature` (string): Feature to analyze (tempo, energy, valence, etc.)
- `groupby` (string): Group by field (genre, artist, year)

## GraphQL API

### Endpoint

```
POST /graphql
```

### Schema Overview

```graphql
type File {
  id: ID!
  path: String!
  size: Int!
  sha256Hash: String!
  xxh128Hash: String!
  modifiedTime: DateTime!
  accessedTime: DateTime!
  changedTime: DateTime!
  createdAt: DateTime!
  eventType: String!
  audioFeatures: AudioFeatures
  videoFeatures: VideoFeatures
  tags: [String!]!
  neighbors: [File!]!
}

type AudioFeatures {
  tempo: Float
  key: String
  mode: String
  timeSignature: Int
  energy: Float
  valence: Float
  acousticness: Float
  instrumentalness: Float
  liveness: Float
  speechiness: Float
  spectralCentroid: Float
  spectralRolloff: Float
  zeroCrossingRate: Float
  mfcc: [Float!]
}

type VideoFeatures {
  duration: Float
  frameRate: Float
  resolution: String
  codec: String
  bitRate: Int
  aspectRatio: String
}

type ProcessingStatus {
  fileId: ID!
  stage: String!
  progress: Float!
  message: String
  completed: Boolean!
  error: String
}

type Query {
  file(id: ID!): File
  fileByPath(path: String!): File
  files(
    limit: Int = 50
    offset: Int = 0
    eventType: String
    startDate: DateTime
    endDate: DateTime
  ): FileConnection!
  searchFiles(query: String!, limit: Int = 50): [File!]!
  processingQueue: [ProcessingStatus!]!
  systemStats: SystemStats!
}

type Mutation {
  uploadFile(file: Upload!, metadata: String): File!
  updateFileTags(fileId: ID!, tags: [String!]!): File!
  reprocessFile(fileId: ID!): ProcessingStatus!
  deleteFile(fileId: ID!): Boolean!
}

type Subscription {
  fileAdded: File!
  processingStatus(fileId: ID!): ProcessingStatus!
  systemStatus: SystemStats!
}
```

### Example Queries

#### Get File with Features

```graphql
query GetFileWithFeatures($fileId: ID!) {
  file(id: $fileId) {
    id
    path
    size
    sha256Hash
    xxh128Hash
    audioFeatures {
      tempo
      energy
      valence
      spectralCentroid
      mfcc
    }
    neighbors {
      path
      size
    }
    tags
  }
}
```

#### Search Files by Path Pattern

```graphql
query SearchFiles($query: String!) {
  searchFiles(query: $query) {
    id
    path
    size
    eventType
    audioFeatures {
      tempo
      key
      energy
    }
    videoFeatures {
      duration
      resolution
      frameRate
    }
  }
}
```

#### Get Processing Queue Status

```graphql
query GetProcessingQueue {
  processingQueue {
    fileId
    stage
    progress
    message
    completed
    error
  }
}
```

#### Real-time Processing Updates

```graphql
subscription ProcessingUpdates($fileId: ID!) {
  processingStatus(fileId: $fileId) {
    stage
    progress
    message
    completed
    error
  }
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// With authentication
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_JWT_TOKEN');
```

### Event Types

#### File Events

```javascript
// New file detected
{
  "type": "file.detected",
  "data": {
    "id": "uuid",
    "path": "/data/music/new_song.mp3",
    "size": 4567890,
    "event_type": "IN_CREATE"
  }
}

// Processing status updates
{
  "type": "processing.update",
  "data": {
    "file_id": "uuid",
    "stage": "feature_extraction",
    "progress": 75,
    "message": "Extracting audio features..."
  }
}

// Analysis completed
{
  "type": "analysis.completed",
  "data": {
    "file_id": "uuid",
    "audio_features": { ... },
    "video_features": { ... }
  }
}

// Neighbor relationship detected
{
  "type": "neighbor.detected",
  "data": {
    "file_id": "uuid",
    "neighbor_id": "neighbor_uuid",
    "relationship": "NEIGHBOR"
  }
}
```

#### System Events

```javascript
// System status
{
  "type": "system.status",
  "data": {
    "queue_size": 5,
    "processing_active": true,
    "services": {
      "ingestor": "healthy",
      "analyzer": "healthy",
      "populator": "healthy",
      "api": "healthy"
    },
    "amqp_status": "connected",
    "neo4j_status": "connected",
    "postgres_status": "connected"
  }
}

// Service health change
{
  "type": "service.health",
  "data": {
    "service": "analyzer",
    "status": "unhealthy",
    "message": "Memory usage exceeded threshold"
  }
}
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authenticated requests**: 1000 requests/hour
- **Unauthenticated requests**: 100 requests/hour
- **Upload endpoints**: 50 uploads/hour
- **Search endpoints**: 200 requests/hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "artist",
      "issue": "Field is required"
    },
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED` - Missing or invalid token
- `PERMISSION_DENIED` - Insufficient permissions
- `VALIDATION_ERROR` - Invalid input data
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `PROCESSING_ERROR` - Error during media processing

## SDK and Examples

### Python SDK

```python
from apollonia_client import ApollonaClient

# Initialize client
client = ApollonaClient(base_url="http://localhost:8000", token="your_jwt_token")

# Get media
media = client.media.list(genre="jazz", limit=10)

# Search
results = client.search("classical piano")

# Upload
with open("song.mp3", "rb") as f:
    media = client.media.upload(
        file=f, metadata={"title": "Song Title", "artist": "Artist"}
    )

# GraphQL query
query = """
query GetMedia($limit: Int!) {
  allMedia(limit: $limit) {
    edges {
      node {
        title
        artist
        audioFeatures {
          tempo
          energy
        }
      }
    }
  }
}
"""
result = client.graphql.query(query, variables={"limit": 5})
```

### JavaScript SDK

```javascript
import { ApollonaClient } from '@apollonia/client';

const client = new ApollonaClient({
  baseUrl: 'http://localhost:8000',
  token: 'your_jwt_token'
});

// Get media
const media = await client.media.list({ genre: 'jazz', limit: 10 });

// WebSocket connection
const ws = client.websocket.connect();
ws.on('media.added', (event) => {
  console.log('New media:', event.data);
});

// GraphQL
const { data } = await client.graphql.query({
  query: gql`
    query GetMedia {
      allMedia(limit: 5) {
        edges {
          node {
            title
            artist
          }
        }
      }
    }
  `
});
```

### cURL Examples

```bash
# Get all media
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/media?limit=10"

# Search for specific artist
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/search?q=artist:Coltrane"

# Get collection statistics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/stats"

# Create a new collection
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Collection","description":"Favorite tracks"}' \
  "http://localhost:8000/api/v1/collections"
```

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Development and Testing

### API Testing

```bash
# Install testing dependencies
pip install httpx pytest

# Run API tests
pytest tests/api/

# Test with different environments
APOLLONIA_ENV=development pytest tests/api/
```

### Mock Data

For development and testing, mock data endpoints are available:

```bash
# Generate sample data
curl -X POST http://localhost:8000/api/v1/dev/generate-sample-data

# Reset database
curl -X POST http://localhost:8000/api/v1/dev/reset-database
```

For more information, see the [Development Guide](../development/development-guide.md).
