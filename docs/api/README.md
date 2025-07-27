# API Documentation

Apollonia provides comprehensive REST and GraphQL APIs for programmatic access to the media catalog
system.

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

- **REST API**: Standard HTTP endpoints for CRUD operations
- **GraphQL API**: Flexible query interface for complex data retrieval
- **WebSocket API**: Real-time updates and streaming
- **Admin API**: Administrative functions and system management

### Base URLs

- **Production**: `https://api.apollonia.example.com`
- **Development**: `http://localhost:8000`
- **GraphQL Endpoint**: `/graphql`
- **REST API Base**: `/api/v1`
- **WebSocket**: `/ws`

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
      "title": "A Love Supreme",
      "similarity": 0.89
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
type Media {
  id: ID!
  title: String!
  artist: String
  album: String
  genre: String
  duration: Int
  filePath: String!
  format: String!
  fileSize: Int
  createdAt: DateTime!
  audioFeatures: AudioFeatures
  technicalAnalysis: TechnicalAnalysis
  tags: [String!]!
  collections: [Collection!]!
  neighbors(limit: Int = 5): [MediaSimilarity!]!
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
}

type Collection {
  id: ID!
  name: String!
  description: String
  isPublic: Boolean!
  media: [Media!]!
  createdAt: DateTime!
}

type Query {
  media(id: ID): Media
  allMedia(
    limit: Int = 50
    offset: Int = 0
    filter: MediaFilter
    sort: MediaSort
  ): MediaConnection!
  searchMedia(query: String!, limit: Int = 50): [Media!]!
  collections: [Collection!]!
  stats: CollectionStats!
}

type Mutation {
  createCollection(input: CreateCollectionInput!): Collection!
  updateMedia(id: ID!, input: UpdateMediaInput!): Media!
  addToCollection(collectionId: ID!, mediaId: ID!): Collection!
}

type Subscription {
  mediaAdded: Media!
  processingStatus(mediaId: ID!): ProcessingStatus!
}
```

### Example Queries

#### Get Media with Features

```graphql
query GetMediaWithFeatures($limit: Int = 10) {
  allMedia(limit: $limit) {
    edges {
      node {
        id
        title
        artist
        genre
        duration
        audioFeatures {
          tempo
          energy
          valence
        }
        tags
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

#### Search with Filters

```graphql
query SearchJazzMusic($query: String!) {
  searchMedia(query: $query) {
    id
    title
    artist
    album
    audioFeatures {
      tempo
      key
      energy
    }
    neighbors(limit: 3) {
      media {
        title
        artist
      }
      similarity
    }
  }
}
```

#### Real-time Processing Updates

```graphql
subscription ProcessingUpdates($mediaId: ID!) {
  processingStatus(mediaId: $mediaId) {
    stage
    progress
    message
    completed
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

#### Media Events

```javascript
// New media added
{
  "type": "media.added",
  "data": {
    "id": "uuid",
    "title": "New Song",
    "artist": "Artist Name"
  }
}

// Processing status updates
{
  "type": "processing.update",
  "data": {
    "media_id": "uuid",
    "stage": "feature_extraction",
    "progress": 75,
    "message": "Extracting audio features..."
  }
}

// Analysis completed
{
  "type": "analysis.completed",
  "data": {
    "media_id": "uuid",
    "features": { ... },
    "technical_analysis": { ... }
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
      "populator": "healthy"
    }
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
