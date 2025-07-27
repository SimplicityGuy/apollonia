# API Service Documentation

The API Service provides the main interface for the Apollonia media catalog system, offering both
REST and GraphQL endpoints for client applications, web interfaces, and third-party integrations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Authentication & Authorization](#authentication--authorization)
- [REST API](#rest-api)
- [GraphQL API](#graphql-api)
- [WebSocket API](#websocket-api)
- [Database Integration](#database-integration)
- [Caching Strategy](#caching-strategy)
- [Performance](#performance)
- [Development](#development)

## Overview

The API service is built with FastAPI and provides:

- **RESTful Endpoints**: Standard HTTP API for CRUD operations
- **GraphQL Interface**: Flexible query language for complex data retrieval
- **WebSocket Support**: Real-time updates and streaming
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Granular permission control
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Rate Limiting**: Protection against abuse
- **Caching**: Redis-based response caching

### Key Features

- **High Performance**: Async/await throughout, optimized database queries
- **Type Safety**: Full Pydantic models and type hints
- **Auto Documentation**: Interactive API docs with examples
- **Monitoring**: Comprehensive logging and metrics
- **Extensible**: Plugin architecture for custom endpoints

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Service                            │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   FastAPI     │  │   GraphQL      │  │   WebSocket    │ │
│  │   REST API    │  │   Endpoint     │  │   Manager      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Auth        │  │   Rate         │  │   Response     │ │
│  │   Manager     │  │   Limiter      │  │   Cache        │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Media       │  │   Search       │  │   Collection   │ │
│  │   Service     │  │   Service      │  │   Service      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   User        │  │   Analytics    │  │   Upload       │ │
│  │   Service     │  │   Service      │  │   Service      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Data Access Layer                      │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  PostgreSQL   │  │     Redis      │  │     Neo4j      │ │
│  │  Repository   │  │     Cache      │  │   Repository   │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```mermaid
graph LR
    A[Client Request] --> B[Rate Limiter]
    B --> C[Authentication]
    C --> D[Authorization]
    D --> E{API Type}

    E -->|REST| F[REST Router]
    E -->|GraphQL| G[GraphQL Resolver]
    E -->|WebSocket| H[WebSocket Handler]

    F --> I[Business Logic]
    G --> I
    H --> I

    I --> J[Data Access Layer]
    J --> K[Cache Check]
    K --> L{Cache Hit?}

    L -->|Yes| M[Return Cached Data]
    L -->|No| N[Database Query]

    N --> O[Cache Update]
    O --> P[Response Formatting]
    M --> P

    P --> Q[Client Response]
```

## Authentication & Authorization

### JWT Authentication

The API uses JSON Web Tokens (JWT) for stateless authentication:

```python
# api/auth/jwt_manager.py
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext


class JWTManager:
    """Manages JWT token creation and validation."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """Create a new access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
```

### Role-Based Access Control (RBAC)

```python
# api/auth/rbac.py
from enum import Enum
from typing import List


class Permission(Enum):
    READ_MEDIA = "read:media"
    WRITE_MEDIA = "write:media"
    DELETE_MEDIA = "delete:media"
    MANAGE_USERS = "manage:users"
    VIEW_ANALYTICS = "view:analytics"
    ADMIN_ACCESS = "admin:access"


class Role(Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    Role.GUEST: [Permission.READ_MEDIA],
    Role.USER: [
        Permission.READ_MEDIA,
        Permission.WRITE_MEDIA,
        Permission.VIEW_ANALYTICS,
    ],
    Role.MODERATOR: [
        Permission.READ_MEDIA,
        Permission.WRITE_MEDIA,
        Permission.DELETE_MEDIA,
        Permission.VIEW_ANALYTICS,
    ],
    Role.ADMIN: list(Permission),  # All permissions
}


def require_permission(permission: Permission):
    """Decorator to require specific permission for endpoint access."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(401, "Authentication required")

            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(403, "Insufficient permissions")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
```

### Authentication Endpoints

```python
# api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from api.schemas.auth import LoginRequest, TokenResponse, UserCreate

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """🔐 Authenticate user and return JWT token."""
    user = await auth_service.authenticate_user(
        credentials.username, credentials.password
    )

    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token, token_type="bearer", expires_in=3600
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)
):
    """📝 Register a new user account."""
    existing_user = await auth_service.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(400, "Username already exists")

    user = await auth_service.create_user(user_data)
    return UserResponse.from_orm(user)


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """🔄 Refresh JWT token."""
    new_token = auth_service.create_access_token(
        data={"sub": current_user.username, "role": current_user.role.value}
    )

    return {"access_token": new_token, "token_type": "bearer"}
```

## REST API

### Core Endpoints

#### Media Management

```python
# api/routers/media.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from typing import Optional, List
from api.schemas.media import MediaResponse, MediaCreate, MediaUpdate, MediaFilter

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/", response_model=PaginatedResponse[MediaResponse])
async def list_media(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    format: Optional[str] = None,
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
):
    """📂 List media files with filtering and pagination."""
    filters = MediaFilter(
        genre=genre, artist=artist, format=format, sort=sort, order=order
    )

    result = await media_service.list_media(
        filters=filters, limit=limit, offset=offset, user_id=current_user.id
    )

    return PaginatedResponse(
        items=result.items, total=result.total, limit=limit, offset=offset
    )


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
):
    """🎵 Get detailed media information."""
    media = await media_service.get_media_by_id(media_id, current_user.id)
    if not media:
        raise HTTPException(404, "Media not found")

    return MediaResponse.from_orm(media)


@router.post("/upload", response_model=MediaResponse)
async def upload_media(
    file: UploadFile,
    metadata: str = None,
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
):
    """📤 Upload a new media file."""
    if not file.content_type.startswith(("audio/", "video/")):
        raise HTTPException(400, "Only audio and video files are supported")

    # Parse metadata if provided
    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid metadata JSON")

    # Process upload
    result = await upload_service.process_upload(
        file=file, metadata=parsed_metadata, user_id=current_user.id
    )

    return MediaResponse.from_orm(result.media)


@router.put("/{media_id}", response_model=MediaResponse)
@require_permission(Permission.WRITE_MEDIA)
async def update_media(
    media_id: str,
    updates: MediaUpdate,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
):
    """✏️ Update media metadata."""
    media = await media_service.update_media(
        media_id=media_id,
        updates=updates.dict(exclude_unset=True),
        user_id=current_user.id,
    )

    if not media:
        raise HTTPException(404, "Media not found")

    return MediaResponse.from_orm(media)


@router.delete("/{media_id}")
@require_permission(Permission.DELETE_MEDIA)
async def delete_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
):
    """🗑️ Delete a media file."""
    success = await media_service.delete_media(media_id, current_user.id)
    if not success:
        raise HTTPException(404, "Media not found")

    return {"message": "Media deleted successfully"}
```

#### Search Endpoints

```python
# api/routers/search.py
@router.get("/", response_model=SearchResponse)
async def search_media(
    q: str = Query(..., min_length=1),
    fields: List[str] = Query(default=["title", "artist", "album"]),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    filters: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    """🔍 Search media files with full-text search."""
    search_params = SearchParams(
        query=q, fields=fields, filters=filters or {}, limit=limit, offset=offset
    )

    results = await search_service.search_media(
        params=search_params, user_id=current_user.id
    )

    return SearchResponse(
        query=q, results=results.items, total=results.total, took_ms=results.duration_ms
    )


@router.get("/suggest")
async def suggest_search(
    q: str = Query(..., min_length=2),
    field: str = Query("title"),
    limit: int = Query(10, le=50),
    search_service: SearchService = Depends(get_search_service),
):
    """💡 Get search suggestions and autocomplete."""
    suggestions = await search_service.get_suggestions(
        query=q, field=field, limit=limit
    )

    return {"suggestions": suggestions}
```

#### Analytics Endpoints

```python
# api/routers/analytics.py
@router.get("/stats", response_model=CollectionStats)
async def get_collection_stats(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """📊 Get collection statistics and overview."""
    stats = await analytics_service.get_collection_stats(current_user.id)
    return CollectionStats.from_orm(stats)


@router.get("/trends")
async def get_trends(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    metric: str = Query("uploads", regex="^(uploads|plays|duration)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """📈 Get trending data and metrics."""
    trends = await analytics_service.get_trends(
        period=period, metric=metric, user_id=current_user.id
    )

    return {"trends": trends, "period": period, "metric": metric}


@router.get("/similar/{media_id}")
async def get_similar_media(
    media_id: str,
    limit: int = Query(10, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """🎯 Get similar media based on audio features."""
    similar = await analytics_service.find_similar_media(
        media_id=media_id, limit=limit, threshold=similarity_threshold
    )

    return {"similar_media": similar}
```

### Data Models

```python
# api/schemas/media.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class MediaBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: Optional[str] = Field(None, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    tags: List[str] = Field(default_factory=list)


class MediaCreate(MediaBase):
    file_path: str = Field(..., min_length=1)
    format: str = Field(..., regex="^(mp3|wav|flac|ogg|mp4|avi|mov)$")


class MediaUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist: Optional[str] = Field(None, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    tags: Optional[List[str]] = None


class AudioFeatures(BaseModel):
    tempo: Optional[float] = None
    key: Optional[str] = None
    mode: Optional[str] = None
    time_signature: Optional[int] = None
    energy: Optional[float] = Field(None, ge=0.0, le=1.0)
    valence: Optional[float] = Field(None, ge=0.0, le=1.0)
    acousticness: Optional[float] = Field(None, ge=0.0, le=1.0)
    instrumentalness: Optional[float] = Field(None, ge=0.0, le=1.0)
    liveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    speechiness: Optional[float] = Field(None, ge=0.0, le=1.0)
    loudness: Optional[float] = None


class MediaResponse(MediaBase):
    id: str
    file_path: str
    format: str
    file_size: int
    duration: Optional[float] = None
    bit_rate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    audio_features: Optional[AudioFeatures] = None
    technical_analysis: Optional[Dict] = None
    similarity_vector: Optional[List[float]] = None

    class Config:
        orm_mode = True
```

## GraphQL API

### Schema Definition

```python
# api/graphql/schema.py
import strawberry
from typing import List, Optional
from api.graphql.types import Media, Collection, User, SearchResult
from api.graphql.resolvers import MediaResolver, CollectionResolver


@strawberry.type
class Query:
    """GraphQL Query root."""

    @strawberry.field
    async def media(self, id: str) -> Optional[Media]:
        """Get media by ID."""
        return await MediaResolver.get_media(id)

    @strawberry.field
    async def all_media(
        self, limit: int = 50, offset: int = 0, filter: Optional[MediaFilter] = None
    ) -> MediaConnection:
        """Get all media with pagination and filtering."""
        return await MediaResolver.get_all_media(limit, offset, filter)

    @strawberry.field
    async def search_media(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search media with full-text search."""
        return await MediaResolver.search_media(query, limit)

    @strawberry.field
    async def collections(self) -> List[Collection]:
        """Get user's collections."""
        return await CollectionResolver.get_collections()

    @strawberry.field
    async def collection_stats(self) -> CollectionStats:
        """Get collection statistics."""
        return await MediaResolver.get_collection_stats()


@strawberry.type
class Mutation:
    """GraphQL Mutation root."""

    @strawberry.mutation
    async def create_collection(self, input: CreateCollectionInput) -> Collection:
        """Create a new collection."""
        return await CollectionResolver.create_collection(input)

    @strawberry.mutation
    async def update_media(self, id: str, input: UpdateMediaInput) -> Media:
        """Update media metadata."""
        return await MediaResolver.update_media(id, input)

    @strawberry.mutation
    async def add_to_collection(self, collection_id: str, media_id: str) -> Collection:
        """Add media to collection."""
        return await CollectionResolver.add_media(collection_id, media_id)


@strawberry.type
class Subscription:
    """GraphQL Subscription root."""

    @strawberry.subscription
    async def media_added(self) -> Media:
        """Subscribe to new media additions."""
        async for media in MediaResolver.media_stream():
            yield media

    @strawberry.subscription
    async def processing_status(self, media_id: str) -> ProcessingStatus:
        """Subscribe to processing status updates."""
        async for status in MediaResolver.processing_stream(media_id):
            yield status
```

### GraphQL Types

```python
# api/graphql/types.py
import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class AudioFeatures:
    tempo: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None


@strawberry.type
class Media:
    id: str
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    format: str
    file_size: int
    created_at: datetime
    audio_features: Optional[AudioFeatures] = None
    tags: List[str]

    @strawberry.field
    async def neighbors(self, limit: int = 5) -> List["MediaSimilarity"]:
        """Get similar media."""
        return await MediaResolver.get_neighbors(self.id, limit)

    @strawberry.field
    async def collections(self) -> List["Collection"]:
        """Get collections containing this media."""
        return await CollectionResolver.get_media_collections(self.id)


@strawberry.type
class Collection:
    id: str
    name: str
    description: Optional[str] = None
    is_public: bool
    created_at: datetime

    @strawberry.field
    async def media(self, limit: Optional[int] = None) -> List[Media]:
        """Get media in this collection."""
        return await CollectionResolver.get_collection_media(self.id, limit)

    @strawberry.field
    async def media_count(self) -> int:
        """Get total media count in collection."""
        return await CollectionResolver.get_media_count(self.id)


@strawberry.input
class MediaFilter:
    genre: Optional[str] = None
    artist: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    duration_min: Optional[float] = None
    duration_max: Optional[float] = None


@strawberry.input
class CreateCollectionInput:
    name: str
    description: Optional[str] = None
    is_public: bool = False
    media_ids: List[str] = strawberry.field(default_factory=list)
```

## WebSocket API

### Connection Management

```python
# api/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio

class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)

        📡 WebSocket connected: client={client_id}, user={user_id}

    def disconnect(self, client_id: str, user_id: str):
        """Remove WebSocket connection."""
        self.active_connections.pop(client_id, None)

        if user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove from all subscriptions
        for event_type in list(self.subscriptions.keys()):
            self.subscriptions[event_type].discard(client_id)

        📡 WebSocket disconnected: client={client_id}, user={user_id}

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))

    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections for a user."""
        if user_id in self.user_connections:
            tasks = []
            for client_id in self.user_connections[user_id]:
                task = self.send_personal_message(message, client_id)
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast(self, message: dict, event_type: str = None):
        """Broadcast message to all subscribed connections."""
        if event_type and event_type in self.subscriptions:
            target_clients = self.subscriptions[event_type]
        else:
            target_clients = self.active_connections.keys()

        tasks = []
        for client_id in target_clients:
            task = self.send_personal_message(message, client_id)
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

    def subscribe(self, client_id: str, event_type: str):
        """Subscribe client to specific event type."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()
        self.subscriptions[event_type].add(client_id)

    def unsubscribe(self, client_id: str, event_type: str):
        """Unsubscribe client from event type."""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(client_id)
```

### WebSocket Endpoints

```python
# api/websocket/endpoints.py
from fastapi import WebSocket, Depends, HTTPException
from api.websocket.manager import ConnectionManager
from api.auth.jwt_manager import JWTManager
import uuid
import json

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    jwt_manager: JWTManager = Depends(get_jwt_manager)
):
    """Main WebSocket endpoint with authentication."""
    # Authenticate user
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    payload = jwt_manager.verify_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    client_id = str(uuid.uuid4())

    await manager.connect(websocket, client_id, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            await handle_websocket_message(message, client_id, user_id)

    except Exception as e:
        ❌ WebSocket error: {e}
    finally:
        manager.disconnect(client_id, user_id)

async def handle_websocket_message(message: dict, client_id: str, user_id: str):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")

    if message_type == "subscribe":
        event_type = message.get("event_type")
        if event_type:
            manager.subscribe(client_id, event_type)
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "event_type": event_type
            }, client_id)

    elif message_type == "unsubscribe":
        event_type = message.get("event_type")
        if event_type:
            manager.unsubscribe(client_id, event_type)

    elif message_type == "ping":
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)
```

### Event Broadcasting

```python
# api/events/broadcaster.py
from api.websocket.manager import ConnectionManager
from typing import Dict, Any


class EventBroadcaster:
    """Broadcasts events to WebSocket clients."""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager

    async def media_added(self, media: Dict[str, Any]):
        """Broadcast new media addition."""
        event = {
            "type": "media.added",
            "data": {
                "id": media["id"],
                "title": media["title"],
                "artist": media["artist"],
                "format": media["format"],
                "created_at": media["created_at"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.manager.broadcast(event, "media.added")

    async def processing_update(self, media_id: str, status: Dict[str, Any]):
        """Broadcast processing status update."""
        event = {
            "type": "processing.update",
            "data": {
                "media_id": media_id,
                "stage": status["stage"],
                "progress": status["progress"],
                "message": status.get("message"),
                "completed": status.get("completed", False),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.manager.broadcast(event, f"processing.{media_id}")

    async def system_status(self, status: Dict[str, Any]):
        """Broadcast system status updates."""
        event = {
            "type": "system.status",
            "data": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.manager.broadcast(event, "system.status")
```

## Database Integration

### Repository Pattern

```python
# api/repositories/media_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from api.models.media import Media
from api.schemas.media import MediaFilter, MediaCreate, MediaUpdate
from typing import List, Optional, Tuple


class MediaRepository:
    """Repository for media data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, media_id: str, user_id: str) -> Optional[Media]:
        """Get media by ID."""
        stmt = select(Media).where(and_(Media.id == media_id, Media.user_id == user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_media(
        self, filters: MediaFilter, limit: int, offset: int, user_id: str
    ) -> Tuple[List[Media], int]:
        """List media with filtering and pagination."""
        # Build base query
        stmt = select(Media).where(Media.user_id == user_id)
        count_stmt = select(func.count(Media.id)).where(Media.user_id == user_id)

        # Apply filters
        if filters.genre:
            filter_condition = Media.genre == filters.genre
            stmt = stmt.where(filter_condition)
            count_stmt = count_stmt.where(filter_condition)

        if filters.artist:
            filter_condition = Media.artist.ilike(f"%{filters.artist}%")
            stmt = stmt.where(filter_condition)
            count_stmt = count_stmt.where(filter_condition)

        if filters.year_min:
            filter_condition = Media.year >= filters.year_min
            stmt = stmt.where(filter_condition)
            count_stmt = count_stmt.where(filter_condition)

        # Apply sorting
        if filters.sort == "title":
            order_col = Media.title
        elif filters.sort == "artist":
            order_col = Media.artist
        elif filters.sort == "duration":
            order_col = Media.duration
        else:
            order_col = Media.created_at

        if filters.order == "desc":
            order_col = order_col.desc()

        stmt = stmt.order_by(order_col)

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute queries
        result = await self.session.execute(stmt)
        count_result = await self.session.execute(count_stmt)

        items = result.scalars().all()
        total = count_result.scalar()

        return items, total

    async def create(self, media_data: MediaCreate, user_id: str) -> Media:
        """Create new media record."""
        media = Media(**media_data.dict(), user_id=user_id, id=str(uuid.uuid4()))

        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)

        return media

    async def update(
        self, media_id: str, updates: dict, user_id: str
    ) -> Optional[Media]:
        """Update media record."""
        stmt = select(Media).where(and_(Media.id == media_id, Media.user_id == user_id))
        result = await self.session.execute(stmt)
        media = result.scalar_one_or_none()

        if not media:
            return None

        for key, value in updates.items():
            setattr(media, key, value)

        media.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(media)

        return media
```

## Caching Strategy

### Redis Integration

```python
# api/cache/redis_cache.py
import redis.asyncio as redis
import json
from typing import Any, Optional
from datetime import timedelta

class RedisCache:
    """Redis-based caching service."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            ⚠️ Cache get error: {e}
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: timedelta = timedelta(hours=1)
    ):
        """Set value in cache with TTL."""
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
        except Exception as e:
            ⚠️ Cache set error: {e}

    async def delete(self, key: str):
        """Delete key from cache."""
        try:
            await self.redis.delete(key)
        except Exception as e:
            ⚠️ Cache delete error: {e}

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            ⚠️ Cache clear pattern error: {e}

# Cache decorators
def cache_response(ttl: timedelta = timedelta(hours=1), key_prefix: str = ""):
    """Decorator to cache API responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached = await redis_cache.get(cache_key)
            if cached:
                return cached

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

## Performance

### Database Optimization

```python
# api/database/optimizations.py
from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession

# Database indexes for performance
media_indexes = [
    Index("idx_media_user_id", "user_id"),
    Index("idx_media_genre", "genre"),
    Index("idx_media_artist", "artist"),
    Index("idx_media_created_at", "created_at"),
    Index("idx_media_duration", "duration"),
    Index("idx_media_search", "title", "artist", "album", postgresql_using="gin"),
]


async def create_database_indexes(session: AsyncSession):
    """Create performance indexes."""
    for index in media_indexes:
        await session.execute(
            text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table}")
        )
```

### Query Optimization

```python
# api/services/media_service.py
from sqlalchemy.orm import selectinload, joinedload


class MediaService:
    """Optimized media service with efficient queries."""

    async def get_media_with_features(self, media_id: str) -> Optional[Media]:
        """Get media with audio features in single query."""
        stmt = (
            select(Media)
            .options(
                selectinload(Media.audio_features),
                selectinload(Media.technical_analysis),
            )
            .where(Media.id == media_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_popular_media(self, limit: int = 50) -> List[Media]:
        """Get popular media with optimized query."""
        stmt = (
            select(Media)
            .options(joinedload(Media.play_stats))
            .order_by(Media.play_count.desc(), Media.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().unique().all()
```

## Development

### Running Locally

```bash
# Install dependencies
cd api
uv sync --all-extras

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/apollonia
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=your_secret_key

# Run development server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run with debugging
uv run uvicorn api.main:app --reload --log-level debug
```

### Testing

```bash
# Run API tests
uv run pytest tests/api/ -v

# Run with coverage
uv run pytest tests/api/ --cov=api --cov-report=html

# Test specific endpoints
uv run pytest tests/api/test_media_endpoints.py -v

# Integration tests
uv run pytest tests/integration/test_api_integration.py -v
```

### API Documentation

The API automatically generates interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Adding New Endpoints

1. **Create Router**:

```python
# api/routers/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/new-feature", tags=["new-feature"])


@router.get("/")
async def list_items():
    return {"items": []}
```

2. **Add to Main App**:

```python
# api/main.py
from api.routers import new_feature

app.include_router(new_feature.router, prefix="/api/v1")
```

3. **Add Tests**:

```python
# tests/api/test_new_feature.py
def test_list_items():
    response = client.get("/api/v1/new-feature/")
    assert response.status_code == 200
```

For more information on development practices, see the
[Development Guide](../development/development-guide.md) and
[Testing Guide](../development/testing.md).
