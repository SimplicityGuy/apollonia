# Performance Tuning Guide

Comprehensive guide for optimizing Apollonia's performance across all components, from database
queries to ML model inference and frontend responsiveness.

## Table of Contents

- [Performance Overview](#performance-overview)
- [Database Performance](#database-performance)
- [API Performance](#api-performance)
- [ML Processing Performance](#ml-processing-performance)
- [Frontend Performance](#frontend-performance)
- [Infrastructure Performance](#infrastructure-performance)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Troubleshooting](#troubleshooting)

## Performance Overview

### Performance Targets

| Component         | Metric          | Target        | Measurement                     |
| ----------------- | --------------- | ------------- | ------------------------------- |
| API Response      | 95th percentile | \<200ms       | Response time for GET requests  |
| Database Queries  | Average         | \<50ms        | Query execution time            |
| File Processing   | Throughput      | >10 files/min | Media analysis pipeline         |
| Frontend Load     | Initial         | \<3s          | Time to interactive             |
| Search Queries    | Response        | \<100ms       | Full-text search results        |
| Upload Processing | Latency         | \<5s          | File upload to processing start |

### Performance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Stack                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Frontend    │  │      API       │  │   ML Pipeline  │ │
│  │  React/Vite   │  │   FastAPI      │  │  TensorFlow    │ │
│  │  Performance  │  │  Performance   │  │  Performance   │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Caching Layer                         │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │     Redis     │  │   Browser      │  │   CDN/Proxy    │ │
│  │     Cache     │  │     Cache      │  │     Cache      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Database Layer                         │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  PostgreSQL   │  │     Neo4j      │  │   File System  │ │
│  │   Indexes     │  │   Indexes      │  │   SSD Storage  │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Database Performance

### PostgreSQL Optimization

#### Index Strategy

```sql
-- Core performance indexes
CREATE INDEX CONCURRENTLY idx_media_user_created
ON media (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_media_search_gin
ON media USING gin(to_tsvector('english', title || ' ' || coalesce(artist, '') || ' ' || coalesce(album, '')));

CREATE INDEX CONCURRENTLY idx_media_genre_artist
ON media (genre, artist) WHERE genre IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_media_audio_features
ON media (id) WHERE audio_features IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_media_duration_genre
ON media (duration, genre) WHERE duration IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_collections_user_public
ON collections (user_id, is_public, created_at DESC);
```

#### Query Optimization

```python
# api/repositories/optimized_queries.py
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload, joinedload


class OptimizedMediaRepository:
    """Repository with performance-optimized queries."""

    async def get_media_with_features_batch(self, media_ids: List[str]) -> List[Media]:
        """Batch load media with features to avoid N+1 queries."""
        stmt = (
            select(Media)
            .options(
                selectinload(Media.audio_features),
                selectinload(Media.technical_analysis),
                selectinload(Media.tags),
            )
            .where(Media.id.in_(media_ids))
        )

        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def search_media_optimized(
        self, query: str, user_id: str, limit: int = 50
    ) -> List[Media]:
        """Optimized full-text search with ranking."""
        # Use PostgreSQL full-text search with ranking
        search_vector = func.to_tsvector(
            "english",
            Media.title
            + " "
            + func.coalesce(Media.artist, "")
            + " "
            + func.coalesce(Media.album, ""),
        )
        search_query = func.plainto_tsquery("english", query)

        stmt = (
            select(Media, func.ts_rank(search_vector, search_query).label("rank"))
            .where(and_(Media.user_id == user_id, search_vector.match(query)))
            .order_by(text("rank DESC"), Media.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_popular_media_cached(self, limit: int = 50) -> List[Media]:
        """Get popular media with optimized query and caching."""
        # Use materialized view for expensive aggregations
        stmt = text(
            """
            SELECT m.* FROM media m
            JOIN media_popularity_mv mp ON m.id = mp.media_id
            ORDER BY mp.popularity_score DESC, m.created_at DESC
            LIMIT :limit
        """
        )

        result = await self.session.execute(stmt, {"limit": limit})
        return result.fetchall()
```

#### Database Configuration

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB                    # 25% of available RAM
effective_cache_size = 1GB               # 75% of available RAM
work_mem = 16MB                          # Per-connection work memory
maintenance_work_mem = 256MB             # For vacuum, index creation
max_connections = 200                    # Adjust based on load
checkpoint_completion_target = 0.9       # Spread checkpoint I/O
wal_buffers = 16MB                       # WAL buffer size
default_statistics_target = 100         # ANALYZE statistics target

-- Enable query logging for analysis
log_min_duration_statement = 1000       # Log slow queries (>1s)
log_statement = 'mod'                   # Log data-modifying statements
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

#### Connection Pooling

```python
# api/database/pool.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool


class DatabasePool:
    """Optimized database connection pool."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            # Connection pool settings
            poolclass=QueuePool,
            pool_size=20,  # Base pool size
            max_overflow=30,  # Additional connections
            pool_pre_ping=True,  # Validate connections
            pool_recycle=3600,  # Recycle connections hourly
            # Query optimization
            echo=False,  # Disable SQL logging in prod
            future=True,  # Use SQLAlchemy 2.0 style
            # Performance settings
            connect_args={
                "command_timeout": 5,
                "server_settings": {
                    "application_name": "apollonia_api",
                    "statement_timeout": "30s",
                },
            },
        )
```

### Neo4j Optimization

```cypher
// Create indexes for relationship queries
CREATE INDEX media_similarity_index FOR ()-[r:SIMILAR_TO]-() ON (r.similarity_score);
CREATE INDEX media_genre_index FOR (m:Media) ON (m.genre);
CREATE INDEX media_artist_index FOR (m:Media) ON (m.artist);

// Optimize similarity queries
MATCH (m1:Media {id: $media_id})-[r:SIMILAR_TO]-(m2:Media)
WHERE r.similarity_score > $threshold
RETURN m2.id, m2.title, r.similarity_score
ORDER BY r.similarity_score DESC
LIMIT $limit;

// Use query hints for complex traversals
MATCH (m:Media)
WHERE m.genre = $genre
WITH m
MATCH (m)-[:SIMILAR_TO]-(similar)
USING INDEX m:Media(genre)
RETURN similar
LIMIT 10;
```

## API Performance

### FastAPI Optimization

#### Async Best Practices

```python
# api/services/async_optimizations.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache


class AsyncOptimizations:
    """Collection of async performance optimizations."""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def parallel_database_queries(self, user_id: str):
        """Execute multiple database queries in parallel."""
        # Execute multiple queries concurrently
        media_task = self.media_repo.get_user_media(user_id)
        collections_task = self.collection_repo.get_user_collections(user_id)
        stats_task = self.analytics_service.get_user_stats(user_id)

        media, collections, stats = await asyncio.gather(
            media_task, collections_task, stats_task, return_exceptions=True
        )

        return {
            "media": media if not isinstance(media, Exception) else [],
            "collections": (
                collections if not isinstance(collections, Exception) else []
            ),
            "stats": stats if not isinstance(stats, Exception) else {},
        }

    async def cpu_intensive_with_executor(self, data: bytes) -> dict:
        """Offload CPU-intensive work to thread executor."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._process_audio_data, data
        )
        return result

    @staticmethod
    def _process_audio_data(data: bytes) -> dict:
        """CPU-intensive audio processing."""
        # Process audio data synchronously
        # This runs in a separate thread
        import librosa
        import numpy as np

        audio, sr = librosa.load(io.BytesIO(data))
        features = {
            "tempo": librosa.beat.tempo(audio, sr=sr)[0],
            "spectral_centroid": np.mean(
                librosa.feature.spectral_centroid(audio, sr=sr)
            ),
            "zero_crossing_rate": np.mean(librosa.feature.zero_crossing_rate(audio)),
        }
        return features
```

#### Response Optimization

```python
# api/middleware/performance.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import gzip


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance optimizations."""

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Timestamp"] = str(int(time.time()))

        # Compress large responses
        if (
            response.headers.get("content-type", "").startswith("application/json")
            and len(response.body) > 1024  # Compress responses > 1KB
        ):
            response.body = gzip.compress(response.body)
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(response.body))

        return response


# Response caching with ETags
from fastapi import Header
from typing import Optional


async def cached_endpoint(if_none_match: Optional[str] = Header(None)):
    """Example of ETag-based caching."""
    # Calculate content hash
    content_hash = calculate_content_hash()
    etag = f'"{content_hash}"'

    # Check if client has current version
    if if_none_match == etag:
        return Response(status_code=304)  # Not Modified

    # Return content with ETag
    response = JSONResponse(content=data)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=300"  # 5 minutes

    return response
```

#### Database Query Optimization

```python
# api/services/query_optimization.py
from sqlalchemy import select
from sqlalchemy.orm import Load


class QueryOptimizer:
    """Optimizes database queries for performance."""

    async def load_media_efficiently(self, media_ids: List[str]):
        """Load media with selective loading to reduce data transfer."""
        # Only load needed columns
        stmt = (
            select(Media)
            .options(
                Load(Media).load_only(
                    Media.id, Media.title, Media.artist, Media.duration, Media.format
                )
            )
            .where(Media.id.in_(media_ids))
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def paginate_efficiently(self, base_query, page: int, per_page: int):
        """Efficient pagination using cursor-based approach."""
        # Use cursor-based pagination for large datasets
        offset = (page - 1) * per_page

        # For large offsets, use cursor-based pagination
        if offset > 10000:
            return await self._cursor_paginate(base_query, page, per_page)
        else:
            return await self._offset_paginate(base_query, offset, per_page)

    async def _cursor_paginate(self, base_query, cursor_id: str, per_page: int):
        """Cursor-based pagination for large datasets."""
        stmt = base_query.where(Media.id > cursor_id).limit(per_page)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### Caching Strategy

#### Redis Configuration

```python
# api/cache/redis_config.py
import redis.asyncio as redis
from typing import Dict, Any
import json
import pickle


class RedisConfig:
    """Optimized Redis configuration."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(
            redis_url,
            # Connection pool settings
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            # Performance settings
            decode_responses=False,  # Handle binary data
            protocol=3,  # Use RESP3 if available
        )

    async def set_with_pipeline(self, items: Dict[str, Any]):
        """Batch set operations using pipeline."""
        pipeline = self.redis.pipeline()

        for key, value in items.items():
            serialized = pickle.dumps(value)  # Faster than JSON for complex objects
            pipeline.setex(key, 3600, serialized)

        await pipeline.execute()

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get operations."""
        pipeline = self.redis.pipeline()

        for key in keys:
            pipeline.get(key)

        results = await pipeline.execute()

        return {
            key: pickle.loads(result) if result else None
            for key, result in zip(keys, results)
        }
```

#### Smart Caching Decorators

```python
# api/cache/decorators.py
from functools import wraps
import hashlib
import json


def cache_with_invalidation(
    ttl: int = 3600, key_prefix: str = "", invalidate_on: List[str] = None
):
    """Advanced caching with automatic invalidation."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try cache first
            cached_result = await redis_cache.get(cache_key)
            if cached_result:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis_cache.setex(cache_key, ttl, result)

            # Set up invalidation triggers
            if invalidate_on:
                for trigger in invalidate_on:
                    await redis_cache.sadd(f"invalidate:{trigger}", cache_key)

            return result

        return wrapper

    return decorator


async def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching pattern."""
    keys = await redis_cache.smembers(f"invalidate:{pattern}")
    if keys:
        await redis_cache.delete(*keys)
        await redis_cache.delete(f"invalidate:{pattern}")
```

## ML Processing Performance

### TensorFlow Optimization

```python
# analyzer/optimizations/tensorflow_config.py
import tensorflow as tf
import os

class TensorFlowOptimizer:
    """TensorFlow performance optimizations."""

    @staticmethod
    def configure_gpu():
        """Configure GPU settings for optimal performance."""
        gpus = tf.config.experimental.list_physical_devices('GPU')

        if gpus:
            try:
                # Enable memory growth
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)

                # Use mixed precision for faster training/inference
                policy = tf.keras.mixed_precision.Policy('mixed_float16')
                tf.keras.mixed_precision.set_global_policy(policy)

                ✅ GPU optimization enabled

            except RuntimeError as e:
                ❌ GPU configuration failed: {e}

    @staticmethod
    def configure_cpu():
        """Configure CPU settings for optimal performance."""
        # Use all available CPU cores
        tf.config.threading.set_intra_op_parallelism_threads(0)
        tf.config.threading.set_inter_op_parallelism_threads(0)

        # Enable XLA compilation
        tf.config.optimizer.set_jit(True)

        # Enable oneDNN optimizations
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '1'
```

### Batch Processing Optimization

```python
# analyzer/processing/batch_optimizer.py
import asyncio
import numpy as np
from typing import List, Dict, Any


class BatchProcessor:
    """Optimized batch processing for ML inference."""

    def __init__(self, batch_size: int = 32, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_files_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple files in optimized batches."""
        # Group files into batches
        batches = [
            file_paths[i : i + self.batch_size]
            for i in range(0, len(file_paths), self.batch_size)
        ]

        # Process batches concurrently
        tasks = [self._process_batch(batch) for batch in batches]

        batch_results = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    async def _process_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of files."""
        async with self.semaphore:
            # Load audio files in parallel
            audio_data = await asyncio.gather(
                *[self._load_audio_async(path) for path in file_paths]
            )

            # Stack into batch tensor
            batch_tensor = np.stack(audio_data)

            # Run inference on entire batch
            features = await self._run_batch_inference(batch_tensor)

            # Split results back to individual files
            return [
                {"file_path": path, "features": feature_dict}
                for path, feature_dict in zip(file_paths, features)
            ]

    async def _run_batch_inference(self, batch_tensor: np.ndarray) -> List[Dict]:
        """Run ML inference on batch."""
        # Preprocess batch
        preprocessed = self._preprocess_batch(batch_tensor)

        # Run all models on batch
        genre_predictions = self.genre_model.predict(preprocessed)
        mood_predictions = self.mood_model.predict(preprocessed)
        instrument_predictions = self.instrument_model.predict(preprocessed)

        # Combine results
        results = []
        for i in range(len(batch_tensor)):
            results.append(
                {
                    "genre": self._decode_genre(genre_predictions[i]),
                    "mood": self._decode_mood(mood_predictions[i]),
                    "instruments": self._decode_instruments(instrument_predictions[i]),
                }
            )

        return results
```

### Model Optimization

```python
# analyzer/models/optimized_models.py
import tensorflow as tf

class OptimizedModels:
    """Model optimization techniques."""

    @staticmethod
    def quantize_model(model_path: str, output_path: str):
        """Quantize model for faster inference."""
        # Load model
        model = tf.keras.models.load_model(model_path)

        # Convert to TensorFlow Lite with quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        # Use representative dataset for better quantization
        converter.representative_dataset = representative_dataset_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8

        tflite_quantized_model = converter.convert()

        # Save quantized model
        with open(output_path, 'wb') as f:
            f.write(tflite_quantized_model)

        🎯 Model quantized and saved to {output_path}

    @staticmethod
    def create_optimized_pipeline(model_paths: List[str]):
        """Create optimized inference pipeline."""
        # Load models with optimization
        models = {}
        for path in model_paths:
            model_name = path.split('/')[-1].split('.')[0]

            # Use TensorFlow Serving for better performance
            if tf.config.list_physical_devices('GPU'):
                # GPU optimization
                model = tf.keras.models.load_model(path)
                model = tf.function(model.call)  # Convert to graph function
                model = model.get_concrete_function(
                    tf.TensorSpec(shape=[None, 128, 128, 1], dtype=tf.float32)
                )
            else:
                # CPU optimization
                model = tf.lite.Interpreter(model_path=path)
                model.allocate_tensors()

            models[model_name] = model

        return models
```

## Frontend Performance

### React Optimization

```typescript
// frontend/src/optimizations/ReactOptimizations.tsx
import React, { memo, useMemo, useCallback, lazy, Suspense } from 'react';
import { VirtualizedList } from './VirtualizedList';

// Lazy load components
const MediaPlayer = lazy(() => import('../components/MediaPlayer'));
const AnalyticsChart = lazy(() => import('../components/AnalyticsChart'));

// Memoized components
const MediaItem = memo(({ media, onPlay, onSelect }) => {
  const handlePlay = useCallback(() => {
    onPlay(media.id);
  }, [media.id, onPlay]);

  const formatDuration = useMemo(() => {
    return formatTime(media.duration);
  }, [media.duration]);

  return (
    <div className="media-item" onClick={handlePlay}>
      <h3>{media.title}</h3>
      <p>{media.artist}</p>
      <span>{formatDuration}</span>
    </div>
  );
});

// Virtualized list for large datasets
const MediaList = ({ mediaItems, onPlay }) => {
  const renderItem = useCallback(({ index, style }) => (
    <div style={style}>
      <MediaItem
        media={mediaItems[index]}
        onPlay={onPlay}
      />
    </div>
  ), [mediaItems, onPlay]);

  return (
    <VirtualizedList
      height={600}
      itemCount={mediaItems.length}
      itemSize={80}
      renderItem={renderItem}
    />
  );
};

// Optimized data fetching
const useOptimizedMediaQuery = (filters) => {
  const queryKey = useMemo(() => ['media', filters], [filters]);

  return useQuery(
    queryKey,
    () => fetchMedia(filters),
    {
      staleTime: 5 * 60 * 1000,  // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      keepPreviousData: true,     // Smooth pagination
    }
  );
};
```

### Bundle Optimization

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { analyzer } from 'vite-bundle-analyzer';

export default defineConfig({
  plugins: [
    react(),
    analyzer({ analyzerMode: 'server' })
  ],
  build: {
    // Code splitting
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@emotion/react'],
          charts: ['recharts', 'd3'],
          audio: ['wavesurfer.js', 'tone']
        }
      }
    },
    // Compression
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    // Enable gzip
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000
  },
  // Development optimizations
  server: {
    hmr: {
      overlay: false  // Reduce HMR overhead
    }
  }
});
```

### Browser Performance

```typescript
// frontend/src/utils/performanceUtils.ts
class PerformanceOptimizer {
  // Debounced search
  static debounceSearch = debounce((query: string, callback: Function) => {
    callback(query);
  }, 300);

  // Image lazy loading with intersection observer
  static setupLazyImages() {
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          img.src = img.dataset.src!;
          img.classList.remove('lazy');
          imageObserver.unobserve(img);
        }
      });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }

  // Optimize audio loading
  static preloadAudio(urls: string[]) {
    const audioCache = new Map();

    urls.forEach(url => {
      const audio = new Audio();
      audio.preload = 'metadata';
      audio.src = url;
      audioCache.set(url, audio);
    });

    return audioCache;
  }

  // Service Worker for caching
  static registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('SW registered:', registration);
        })
        .catch(error => {
          console.log('SW registration failed:', error);
        });
    }
  }
}
```

## Infrastructure Performance

### Docker Optimization

```dockerfile
# Dockerfile optimizations
FROM node:18-alpine AS frontend-builder

# Use multi-stage builds
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .
RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Optimize for performance
RUN apk add --no-cache gzip
```

```nginx
# nginx.conf optimizations
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/javascript
        application/json
        text/css
        text/plain
        text/xml;

    # Enable HTTP/2
    listen 443 ssl http2;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Enable keep-alive
    keepalive_timeout 65;
    keepalive_requests 100;
}
```

### Resource Limits

```yaml
# docker-compose.yml resource limits
version: '3.8'
services:
  api:
    image: apollonia-api
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    environment:
      - WORKERS=4
      - MAX_CONNECTIONS=200

  analyzer:
    image: apollonia-analyzer
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
    environment:
      - BATCH_SIZE=16
      - GPU_MEMORY_FRACTION=0.8
```

## Monitoring and Profiling

### Performance Monitoring

```python
# api/monitoring/performance_monitor.py
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps

# Metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)

            # Log slow operations
            if duration > 1.0:
                ⚠️ Slow operation: {func.__name__} took {duration:.2f}s

    return wrapper

class SystemMonitor:
    """Monitor system resources."""

    @staticmethod
    def update_metrics():
        """Update system metrics."""
        # Memory usage
        memory = psutil.virtual_memory()
        MEMORY_USAGE.set(memory.used)

        # CPU usage
        cpu_percent = psutil.cpu_percent()
        CPU_USAGE.set(cpu_percent)

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            DISK_READ_BYTES.set(disk_io.read_bytes)
            DISK_WRITE_BYTES.set(disk_io.write_bytes)
```

### Query Performance Analysis

```python
# api/monitoring/query_analyzer.py
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

class QueryAnalyzer:
    """Analyze database query performance."""

    def __init__(self):
        self.slow_queries = []
        self.query_stats = {}

    def setup_query_monitoring(self, engine: Engine):
        """Set up query performance monitoring."""
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time

            # Log slow queries
            if total > 0.1:  # 100ms threshold
                self.slow_queries.append({
                    'statement': statement,
                    'duration': total,
                    'timestamp': time.time()
                })

                ⚠️ Slow query ({total:.3f}s): {statement[:100]}...

            # Track query statistics
            query_type = statement.strip().split()[0].upper()
            if query_type not in self.query_stats:
                self.query_stats[query_type] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0
                }

            stats = self.query_stats[query_type]
            stats['count'] += 1
            stats['total_time'] += total
            stats['avg_time'] = stats['total_time'] / stats['count']
```

### Application Profiling

```python
# api/profiling/profiler.py
import cProfile
import pstats
import io
from functools import wraps

class ApplicationProfiler:
    """Profile application performance."""

    @staticmethod
    def profile_function(func):
        """Decorator to profile function execution."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                pr.disable()

                # Analyze results
                s = io.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
                ps.print_stats(10)  # Top 10 functions

                📊 Profile for {func.__name__}:
                {s.getvalue()}

        return wrapper

    @staticmethod
    def memory_profile(func):
        """Monitor memory usage during function execution."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import tracemalloc

            tracemalloc.start()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                💾 Memory usage for {func.__name__}: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB

        return wrapper
```

## Troubleshooting

### Common Performance Issues

#### Slow Database Queries

```bash
# Identify slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'media'
ORDER BY n_distinct DESC;

# Analyze query execution plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM media
WHERE genre = 'jazz'
ORDER BY created_at DESC
LIMIT 50;
```

#### Memory Leaks

```python
# Monitor memory usage
import gc
import psutil


def debug_memory_usage():
    """Debug memory usage and potential leaks."""
    # Force garbage collection
    gc.collect()

    # Get memory info
    process = psutil.Process()
    memory_info = process.memory_info()

    print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.1f} MB")

    # Check object counts
    object_counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        object_counts[obj_type] = object_counts.get(obj_type, 0) + 1

    # Show top object types
    top_objects = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for obj_type, count in top_objects:
        print(f"{obj_type}: {count}")
```

#### High CPU Usage

```bash
# Monitor CPU usage by process
top -p $(pgrep -f apollonia)

# Profile Python application
python -m cProfile -o profile_output.prof api/main.py

# Analyze profile results
python -c "
import pstats
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

### Performance Testing

```python
# tests/performance/load_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor


class LoadTester:
    """Load testing for API endpoints."""

    async def load_test_endpoint(self, url: str, concurrent_requests: int = 100):
        """Test endpoint under load."""

        async def make_request(session):
            start_time = time.time()
            async with session.get(url) as response:
                await response.text()
                return time.time() - start_time

        async with aiohttp.ClientSession() as session:
            # Make concurrent requests
            tasks = [make_request(session) for _ in range(concurrent_requests)]
            response_times = await asyncio.gather(*tasks)

        # Analyze results
        avg_time = sum(response_times) / len(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]

        print(f"Average response time: {avg_time:.3f}s")
        print(f"95th percentile: {p95_time:.3f}s")
        print(f"Requests per second: {concurrent_requests / max(response_times):.1f}")

        return {
            "avg_time": avg_time,
            "p95_time": p95_time,
            "rps": concurrent_requests / max(response_times),
        }


# Run load tests
async def run_performance_tests():
    tester = LoadTester()

    # Test key endpoints
    endpoints = [
        "http://localhost:8000/api/v1/media",
        "http://localhost:8000/api/v1/search?q=test",
        "http://localhost:8000/api/v1/stats",
    ]

    for endpoint in endpoints:
        print(f"\nTesting {endpoint}:")
        results = await tester.load_test_endpoint(endpoint)

        # Performance assertions
        assert (
            results["avg_time"] < 0.5
        ), f"Average response time too high: {results['avg_time']}"
        assert (
            results["p95_time"] < 1.0
        ), f"95th percentile too high: {results['p95_time']}"
        assert results["rps"] > 10, f"RPS too low: {results['rps']}"
```

For more performance monitoring and optimization techniques, see the
[Monitoring Guide](monitoring.md) and [Development Guide](../development/development-guide.md).
