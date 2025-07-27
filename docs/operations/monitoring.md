# Monitoring and Observability Guide

Comprehensive monitoring and observability setup for the Apollonia media catalog system, covering
metrics, logging, alerting, and distributed tracing.

## Table of Contents

- [Monitoring Overview](#monitoring-overview)
- [Metrics Collection](#metrics-collection)
- [Logging Strategy](#logging-strategy)
- [Distributed Tracing](#distributed-tracing)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Health Checks](#health-checks)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## Monitoring Overview

### Observability Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Observability Stack                     │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Grafana     │  │   Jaeger       │  │   ELK Stack    │ │
│  │ Dashboards    │  │   Tracing      │  │   Logging      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Data Collection                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  Prometheus   │  │   OpenTelemetry│  │   Fluent Bit   │ │
│  │   Metrics     │  │    Traces      │  │     Logs       │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ FastAPI       │  │   Analyzer     │  │   Frontend     │ │
│  │ Metrics       │  │   Metrics      │  │   Metrics      │ │
│  └───────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Monitoring Principles

1. **Three Pillars**: Metrics, logs, and traces work together
1. **Proactive Monitoring**: Detect issues before users experience them
1. **Business Metrics**: Monitor user experience and business outcomes
1. **Standardized Instrumentation**: Consistent metrics across services
1. **Automated Alerting**: Smart alerts that reduce noise

## Metrics Collection

### Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Apollonia API Service
  - job_name: 'apollonia-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Analyzer Service
  - job_name: 'apollonia-analyzer'
    static_configs:
      - targets: ['analyzer:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # RabbitMQ
  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq:15692']
    metrics_path: '/metrics'

  # Node Exporter (System Metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # cAdvisor (Container Metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

### Application Metrics

```python
# api/monitoring/metrics.py
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
)
import time
from functools import wraps

# Create metrics registry
registry = CollectorRegistry()

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Business Metrics
media_files_total = Gauge(
    "media_files_total",
    "Total number of media files",
    ["user_id", "format"],
    registry=registry,
)

media_processing_duration_seconds = Histogram(
    "media_processing_duration_seconds",
    "Time taken to process media files",
    ["stage", "format"],
    registry=registry,
)

media_upload_size_bytes = Histogram(
    "media_upload_size_bytes",
    "Size of uploaded media files",
    ["format"],
    registry=registry,
)

# Queue Metrics
queue_messages_total = Gauge(
    "queue_messages_total",
    "Number of messages in queue",
    ["queue_name"],
    registry=registry,
)

# Database Metrics
database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["query_type", "table"],
    registry=registry,
)

database_connections_active = Gauge(
    "database_connections_active", "Active database connections", registry=registry
)

# Cache Metrics
cache_operations_total = Counter(
    "cache_operations_total",
    "Total cache operations",
    ["operation", "result"],
    registry=registry,
)

cache_hit_ratio = Gauge("cache_hit_ratio", "Cache hit ratio", registry=registry)

# ML Processing Metrics
ml_inference_duration_seconds = Histogram(
    "ml_inference_duration_seconds",
    "ML model inference duration",
    ["model_name", "batch_size"],
    registry=registry,
)

ml_model_accuracy = Gauge(
    "ml_model_accuracy",
    "ML model accuracy score",
    ["model_name", "version"],
    registry=registry,
)


def track_request_metrics(func):
    """Decorator to track HTTP request metrics."""

    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        method = request.method
        endpoint = request.url.path
        start_time = time.time()

        try:
            response = await func(request, *args, **kwargs)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

    return wrapper


class MetricsCollector:
    """Collects and updates business metrics."""

    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client

    async def update_media_metrics(self):
        """Update media-related metrics."""
        # Count media files by format
        media_counts = await self.db.execute(
            """
            SELECT format, COUNT(*) as count
            FROM media
            GROUP BY format
        """
        )

        for row in media_counts:
            media_files_total.labels(user_id="all", format=row.format).set(row.count)

    async def update_queue_metrics(self):
        """Update queue metrics from RabbitMQ."""
        # This would integrate with RabbitMQ management API
        queue_info = await self.get_queue_info()

        for queue_name, message_count in queue_info.items():
            queue_messages_total.labels(queue_name=queue_name).set(message_count)

    async def update_cache_metrics(self):
        """Update cache hit ratio."""
        info = await self.redis.info()
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)

        if hits + misses > 0:
            hit_ratio = hits / (hits + misses)
            cache_hit_ratio.set(hit_ratio)
```

### Custom Metrics for ML Pipeline

```python
# analyzer/monitoring/ml_metrics.py
from prometheus_client import Histogram, Counter, Gauge
import time
from functools import wraps

# ML-specific metrics
ml_feature_extraction_duration = Histogram(
    "ml_feature_extraction_duration_seconds",
    "Feature extraction duration",
    ["feature_type", "audio_format"],
)

ml_model_prediction_duration = Histogram(
    "ml_model_prediction_duration_seconds",
    "Model prediction duration",
    ["model_name", "input_size"],
)

ml_processing_errors_total = Counter(
    "ml_processing_errors_total", "Total ML processing errors", ["error_type", "stage"]
)

ml_batch_size = Histogram(
    "ml_batch_size", "Batch size for ML processing", ["model_name"]
)

ml_memory_usage_bytes = Gauge(
    "ml_memory_usage_bytes", "Memory usage during ML processing", ["stage"]
)


def track_ml_metrics(model_name: str):
    """Decorator to track ML processing metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            batch_size = len(args[0]) if args and hasattr(args[0], "__len__") else 1

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                ml_processing_errors_total.labels(
                    error_type=type(e).__name__, stage=func.__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time

                ml_model_prediction_duration.labels(
                    model_name=model_name, input_size=batch_size
                ).observe(duration)

                ml_batch_size.labels(model_name=model_name).observe(batch_size)

        return wrapper

    return decorator


class MLMetricsCollector:
    """Collects ML-specific metrics."""

    def __init__(self):
        self.model_metrics = {}

    def record_feature_extraction(
        self, feature_type: str, duration: float, audio_format: str
    ):
        """Record feature extraction metrics."""
        ml_feature_extraction_duration.labels(
            feature_type=feature_type, audio_format=audio_format
        ).observe(duration)

    def record_memory_usage(self, stage: str, memory_bytes: int):
        """Record memory usage."""
        ml_memory_usage_bytes.labels(stage=stage).set(memory_bytes)

    def update_model_accuracy(self, model_name: str, version: str, accuracy: float):
        """Update model accuracy metrics."""
        ml_model_accuracy.labels(model_name=model_name, version=version).set(accuracy)
```

## Logging Strategy

### Structured Logging Configuration

```python
# shared/logging_config.py
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if hasattr(record, "media_id"):
            log_entry["media_id"] = record.media_id

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """Set up structured logging for a service."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # Add service name to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


# Context manager for request-scoped logging
from contextvars import ContextVar
import uuid

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class LoggingContext:
    """Context manager for request-scoped logging context."""

    def __init__(
        self, request_id: str = None, user_id: str = None, trace_id: str = None
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.trace_id = trace_id

    def __enter__(self):
        request_id_var.set(self.request_id)
        if self.user_id:
            user_id_var.set(self.user_id)
        if self.trace_id:
            trace_id_var.set(self.trace_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        request_id_var.set("")
        user_id_var.set("")
        trace_id_var.set("")


def get_contextual_logger(name: str) -> logging.Logger:
    """Get logger with request context."""
    logger = logging.getLogger(name)

    # Add context to log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.trace_id = trace_id_var.get()
        return record

    logging.setLogRecordFactory(record_factory)

    return logger
```

### Fluent Bit Configuration

```yaml
# monitoring/fluent-bit/fluent-bit.conf
[SERVICE]
    Flush         5
    Daemon        off
    Log_Level     info
    Parsers_File  parsers.conf

[INPUT]
    Name              tail
    Path              /var/log/apollonia/*.log
    Parser            json
    Tag               apollonia.*
    Refresh_Interval  5
    Mem_Buf_Limit     50MB

[INPUT]
    Name              systemd
    Tag               systemd.*
    Systemd_Filter    _SYSTEMD_UNIT=apollonia-api.service
    Systemd_Filter    _SYSTEMD_UNIT=apollonia-analyzer.service

[FILTER]
    Name                modify
    Match               apollonia.*
    Add                 cluster_name ${CLUSTER_NAME}
    Add                 environment ${ENVIRONMENT}

[FILTER]
    Name                grep
    Match               apollonia.*
    Regex               level (ERROR|WARN|INFO)

[OUTPUT]
    Name                elasticsearch
    Match               apollonia.*
    Host                elasticsearch
    Port                9200
    Index               apollonia-logs
    Type                _doc
    Logstash_Format     On
    Logstash_Prefix     apollonia
    Time_Key            @timestamp
    Generate_ID         On

[OUTPUT]
    Name                prometheus_exporter
    Match               apollonia.*
    Host                0.0.0.0
    Port                2021
    Add_label           service $service
    Add_label           level $level
```

### Application Logging

```python
# api/middleware/logging_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract user info if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id

        # Set up logging context
        with LoggingContext(request_id=request_id, user_id=user_id):
            logger = get_contextual_logger(__name__)

            start_time = time.time()

            # Log request
            logger.info(
                "🌐 HTTP request started",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                },
            )

            try:
                response = await call_next(request)

                duration = time.time() - start_time

                # Log response
                logger.info(
                    "✅ HTTP request completed",
                    extra={
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "response_size": (
                            len(response.body) if hasattr(response, "body") else 0
                        ),
                    },
                )

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

                return response

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    "❌ HTTP request failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration * 1000, 2),
                    },
                    exc_info=True,
                )

                raise
```

## Distributed Tracing

### OpenTelemetry Configuration

```python
# api/tracing/opentelemetry_config.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def setup_tracing(service_name: str, jaeger_endpoint: str):
    """Set up distributed tracing with OpenTelemetry."""

    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
        collector_endpoint=jaeger_endpoint,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    return tracer


def instrument_app(app, service_name: str):
    """Instrument FastAPI app with OpenTelemetry."""

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app, service_name=service_name, skip_urls=["metrics", "health"]
    )

    # Auto-instrument database
    SQLAlchemyInstrumentor().instrument()

    # Auto-instrument Redis
    RedisInstrumentor().instrument()

    # Auto-instrument HTTP requests
    RequestsInstrumentor().instrument()


# Custom tracing decorators
def trace_function(operation_name: str = None):
    """Decorator to add tracing to functions."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)

            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Add arguments (be careful with sensitive data)
                if args:
                    span.set_attribute("function.args_count", len(args))
                if kwargs:
                    span.set_attribute("function.kwargs_count", len(kwargs))

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, description=str(e))
                    )
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


class TracingContextManager:
    """Context manager for manual span creation."""

    def __init__(self, operation_name: str, attributes: dict = None):
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.tracer = trace.get_tracer(__name__)
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.operation_name)

        # Add attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.set_status(
                trace.Status(trace.StatusCode.ERROR, description=str(exc_val))
            )
            self.span.record_exception(exc_val)
        else:
            self.span.set_status(trace.Status(trace.StatusCode.OK))

        self.span.end()
```

### Trace Correlation

```python
# shared/trace_correlation.py
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import aiohttp


class TraceCorrelation:
    """Handles trace correlation across service boundaries."""

    @staticmethod
    def inject_trace_headers(headers: dict) -> dict:
        """Inject trace context into HTTP headers."""
        propagator = TraceContextTextMapPropagator()
        propagator.inject(headers)
        return headers

    @staticmethod
    def extract_trace_context(headers: dict):
        """Extract trace context from HTTP headers."""
        propagator = TraceContextTextMapPropagator()
        context = propagator.extract(headers)
        return context

    @staticmethod
    async def traced_http_request(url: str, method: str = "GET", **kwargs):
        """Make HTTP request with trace propagation."""
        headers = kwargs.get("headers", {})

        # Inject trace context
        TraceCorrelation.inject_trace_headers(headers)
        kwargs["headers"] = headers

        # Make request with tracing
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(f"http_{method.lower()}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)

            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    span.set_attribute("http.status_code", response.status)

                    if response.status >= 400:
                        span.set_status(
                            trace.Status(
                                trace.StatusCode.ERROR,
                                description=f"HTTP {response.status}",
                            )
                        )

                    return await response.json()
```

## Alerting

### Alertmanager Configuration

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@apollonia.com'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/webhook'

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@apollonia.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts-critical'
    title: 'Critical Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'warning-alerts'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts-warning'
    title: 'Warning Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Alert Rules

```yaml
# monitoring/prometheus/rules/api_alerts.yml
groups:
- name: api.rules
  rules:

  # High Error Rate
  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
      service: api
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.service }}"

  # High Response Time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
      service: api
    annotations:
      summary: "High response time"
      description: "95th percentile response time is {{ $value }}s"

  # Service Down
  - alert: ServiceDown
    expr: up{job="apollonia-api"} == 0
    for: 1m
    labels:
      severity: critical
      service: api
    annotations:
      summary: "Service is down"
      description: "{{ $labels.job }} service is not responding"

- name: database.rules
  rules:

  # High Database Connections
  - alert: HighDatabaseConnections
    expr: database_connections_active > 80
    for: 2m
    labels:
      severity: warning
      service: database
    annotations:
      summary: "High database connections"
      description: "Database has {{ $value }} active connections"

  # Slow Database Queries
  - alert: SlowDatabaseQueries
    expr: histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
      service: database
    annotations:
      summary: "Slow database queries"
      description: "95th percentile query time is {{ $value }}s"

- name: ml.rules
  rules:

  # ML Processing Backlog
  - alert: MLProcessingBacklog
    expr: queue_messages_total{queue_name="analyzer_queue"} > 100
    for: 10m
    labels:
      severity: warning
      service: analyzer
    annotations:
      summary: "ML processing backlog"
      description: "{{ $value }} files waiting for analysis"

  # High ML Processing Errors
  - alert: HighMLProcessingErrors
    expr: rate(ml_processing_errors_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
      service: analyzer
    annotations:
      summary: "High ML processing error rate"
      description: "ML processing error rate is {{ $value | humanizePercentage }}"

- name: business.rules
  rules:

  # Low Upload Rate
  - alert: LowUploadRate
    expr: rate(media_upload_size_bytes_count[1h]) < 1
    for: 30m
    labels:
      severity: warning
      service: business
    annotations:
      summary: "Low upload activity"
      description: "Only {{ $value }} uploads in the last hour"

  # Cache Hit Rate Too Low
  - alert: LowCacheHitRate
    expr: cache_hit_ratio < 0.8
    for: 10m
    labels:
      severity: warning
      service: cache
    annotations:
      summary: "Low cache hit rate"
      description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

### Smart Alerting

```python
# monitoring/alerting/smart_alerts.py
from typing import Dict, List
import asyncio
from datetime import datetime, timedelta


class SmartAlertManager:
    """Intelligent alert management to reduce noise."""

    def __init__(self):
        self.alert_history = {}
        self.suppression_rules = {}
        self.escalation_rules = {}

    async def process_alert(self, alert: Dict) -> bool:
        """Process alert with smart filtering."""
        alert_key = self._get_alert_key(alert)

        # Check if alert should be suppressed
        if await self._should_suppress(alert_key, alert):
            return False

        # Check for duplicate alerts
        if await self._is_duplicate(alert_key, alert):
            return False

        # Apply rate limiting
        if await self._is_rate_limited(alert_key):
            return False

        # Record alert
        self.alert_history[alert_key] = {
            "last_seen": datetime.now(),
            "count": self.alert_history.get(alert_key, {}).get("count", 0) + 1,
            "alert": alert,
        }

        return True

    async def _should_suppress(self, alert_key: str, alert: Dict) -> bool:
        """Check if alert should be suppressed."""
        # Suppress during maintenance windows
        if await self._is_maintenance_window():
            return True

        # Suppress if dependent service is down
        if await self._check_dependencies(alert):
            return True

        # Suppress if similar alert is already active
        if await self._has_active_similar_alert(alert_key):
            return True

        return False

    async def _is_duplicate(self, alert_key: str, alert: Dict) -> bool:
        """Check if alert is a duplicate."""
        if alert_key in self.alert_history:
            last_alert = self.alert_history[alert_key]
            time_diff = datetime.now() - last_alert["last_seen"]

            # If same alert within 5 minutes, consider duplicate
            if time_diff < timedelta(minutes=5):
                return True

        return False

    async def _is_rate_limited(self, alert_key: str) -> bool:
        """Apply rate limiting to prevent spam."""
        if alert_key in self.alert_history:
            alert_info = self.alert_history[alert_key]

            # If more than 10 alerts in last hour, rate limit
            if alert_info["count"] > 10:
                time_diff = datetime.now() - alert_info["last_seen"]
                if time_diff < timedelta(hours=1):
                    return True

        return False

    def _get_alert_key(self, alert: Dict) -> str:
        """Generate unique key for alert."""
        return (
            f"{alert.get('alertname')}:{alert.get('service')}:{alert.get('instance')}"
        )


# Alert correlation
class AlertCorrelation:
    """Correlate related alerts to reduce noise."""

    def __init__(self):
        self.correlation_rules = {
            "service_down": ["high_error_rate", "high_response_time"],
            "database_down": ["database_connection_error", "slow_queries"],
            "high_memory": ["gc_pressure", "out_of_memory"],
        }

    async def correlate_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """Group related alerts together."""
        correlated_groups = {}
        standalone_alerts = []

        for alert in alerts:
            alert_name = alert.get("alertname")

            # Find correlation group
            group_key = None
            for primary, related in self.correlation_rules.items():
                if alert_name == primary or alert_name in related:
                    group_key = primary
                    break

            if group_key:
                if group_key not in correlated_groups:
                    correlated_groups[group_key] = []
                correlated_groups[group_key].append(alert)
            else:
                standalone_alerts.append(alert)

        # Create combined alerts for correlated groups
        combined_alerts = []
        for group_key, group_alerts in correlated_groups.items():
            if len(group_alerts) > 1:
                combined_alert = {
                    "alertname": f"correlated_{group_key}",
                    "summary": f"Multiple related issues detected: {group_key}",
                    "related_alerts": group_alerts,
                    "severity": max(
                        alert.get("severity", "info") for alert in group_alerts
                    ),
                }
                combined_alerts.append(combined_alert)
            else:
                combined_alerts.extend(group_alerts)

        combined_alerts.extend(standalone_alerts)

        return combined_alerts
```

## Dashboards

### Grafana Dashboard Configuration

```json
// monitoring/grafana/dashboards/apollonia_overview.json
{
  "dashboard": {
    "title": "Apollonia Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "singlestat",
        "targets": [
          {
            "expr": "count(count by (user_id) (rate(http_requests_total[5m])))",
            "legendFormat": "Active Users"
          }
        ]
      },
      {
        "title": "Media Processing Queue",
        "type": "graph",
        "targets": [
          {
            "expr": "queue_messages_total{queue_name=\"analyzer_queue\"}",
            "legendFormat": "Queue Size"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(database_query_duration_seconds_sum[5m]) / rate(database_query_duration_seconds_count[5m])",
            "legendFormat": "Avg Query Time"
          }
        ]
      }
    ]
  }
}
```

### Business Metrics Dashboard

```json
// monitoring/grafana/dashboards/business_metrics.json
{
  "dashboard": {
    "title": "Apollonia Business Metrics",
    "panels": [
      {
        "title": "Total Media Files",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(media_files_total)",
            "legendFormat": "Total Files"
          }
        ]
      },
      {
        "title": "Upload Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(media_upload_size_bytes_count[1h])",
            "legendFormat": "Uploads per hour"
          }
        ]
      },
      {
        "title": "File Formats Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (format) (media_files_total)",
            "legendFormat": "{{format}}"
          }
        ]
      },
      {
        "title": "Processing Time by Format",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(media_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "{{format}} - 95th percentile"
          }
        ]
      }
    ]
  }
}
```

## Health Checks

### Comprehensive Health Check System

```python
# api/health/health_checks.py
from enum import Enum
from typing import Dict, List, Optional
import asyncio
import time
import aiohttp


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    async def check(self) -> Dict:
        """Perform health check."""
        start_time = time.time()

        try:
            result = await asyncio.wait_for(self._perform_check(), timeout=self.timeout)

            duration = time.time() - start_time

            return {
                "name": self.name,
                "status": HealthStatus.HEALTHY.value,
                "duration_ms": round(duration * 1000, 2),
                "details": result,
            }

        except asyncio.TimeoutError:
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY.value,
                "error": "Timeout",
                "duration_ms": self.timeout * 1000,
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2),
            }

    async def _perform_check(self) -> Dict:
        """Override this method to implement specific check."""
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity health check."""

    def __init__(self, db_session):
        super().__init__("database")
        self.db_session = db_session

    async def _perform_check(self) -> Dict:
        # Simple query to test connectivity
        result = await self.db_session.execute("SELECT 1")

        # Check connection pool status
        pool_info = {
            "pool_size": self.db_session.bind.pool.size(),
            "checked_in": self.db_session.bind.pool.checkedin(),
            "checked_out": self.db_session.bind.pool.checkedout(),
            "overflow": self.db_session.bind.pool.overflow(),
            "invalid": self.db_session.bind.pool.invalid(),
        }

        return {"query_result": result.scalar(), "pool_info": pool_info}


class RedisHealthCheck(HealthCheck):
    """Redis connectivity health check."""

    def __init__(self, redis_client):
        super().__init__("redis")
        self.redis = redis_client

    async def _perform_check(self) -> Dict:
        # Test basic operations
        test_key = "health_check_test"
        test_value = str(time.time())

        await self.redis.set(test_key, test_value, ex=60)
        retrieved_value = await self.redis.get(test_key)
        await self.redis.delete(test_key)

        # Get Redis info
        info = await self.redis.info()

        return {
            "test_passed": retrieved_value.decode() == test_value,
            "memory_usage": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
        }


class QueueHealthCheck(HealthCheck):
    """Message queue health check."""

    def __init__(self, queue_manager):
        super().__init__("message_queue")
        self.queue_manager = queue_manager

    async def _perform_check(self) -> Dict:
        # Check queue status
        queue_info = await self.queue_manager.get_queue_info()

        # Check if consumers are active
        consumer_count = await self.queue_manager.get_consumer_count()

        return {
            "queue_info": queue_info,
            "active_consumers": consumer_count,
            "connection_status": "connected",
        }


class ExternalServiceHealthCheck(HealthCheck):
    """External service health check."""

    def __init__(self, service_name: str, url: str):
        super().__init__(f"external_{service_name}")
        self.service_name = service_name
        self.url = url

    async def _perform_check(self) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                return {
                    "status_code": response.status,
                    "response_time_ms": response.headers.get("X-Response-Time"),
                    "service_available": response.status < 500,
                }


class HealthCheckManager:
    """Manages all health checks."""

    def __init__(self):
        self.health_checks: List[HealthCheck] = []
        self.last_check_results = {}
        self.last_check_time = None

    def register_check(self, health_check: HealthCheck):
        """Register a health check."""
        self.health_checks.append(health_check)

    async def run_all_checks(self) -> Dict:
        """Run all health checks."""
        tasks = [check.check() for check in self.health_checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        check_results = {}
        overall_status = HealthStatus.HEALTHY

        for result in results:
            if isinstance(result, Exception):
                check_results["unknown_error"] = {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": str(result),
                }
                overall_status = HealthStatus.UNHEALTHY
            else:
                check_results[result["name"]] = result

                if result["status"] == HealthStatus.UNHEALTHY.value:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    result["status"] == HealthStatus.DEGRADED.value
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED

        self.last_check_results = check_results
        self.last_check_time = time.time()

        return {
            "status": overall_status.value,
            "timestamp": self.last_check_time,
            "checks": check_results,
            "summary": {
                "total_checks": len(self.health_checks),
                "healthy": len(
                    [
                        r
                        for r in check_results.values()
                        if r.get("status") == HealthStatus.HEALTHY.value
                    ]
                ),
                "degraded": len(
                    [
                        r
                        for r in check_results.values()
                        if r.get("status") == HealthStatus.DEGRADED.value
                    ]
                ),
                "unhealthy": len(
                    [
                        r
                        for r in check_results.values()
                        if r.get("status") == HealthStatus.UNHEALTHY.value
                    ]
                ),
            },
        }
```

### Health Check Endpoints

```python
# api/routers/health.py
from fastapi import APIRouter, Depends
from api.health.health_checks import HealthCheckManager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    health_manager: HealthCheckManager = Depends(get_health_manager),
):
    """🏥 Comprehensive health check endpoint."""
    return await health_manager.run_all_checks()


@router.get("/health/live")
async def liveness_check():
    """💓 Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/health/ready")
async def readiness_check(
    health_manager: HealthCheckManager = Depends(get_health_manager),
):
    """✅ Kubernetes readiness probe."""
    results = await health_manager.run_all_checks()

    if results["status"] == "unhealthy":
        raise HTTPException(503, "Service not ready")

    return {"status": "ready", "timestamp": time.time()}
```

## Troubleshooting

### Log Analysis Tools

```python
# monitoring/tools/log_analyzer.py
import re
from typing import Dict, List
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class LogAnalyzer:
    """Analyze logs for patterns and issues."""

    def __init__(self, logs: List[str]):
        self.logs = logs
        self.parsed_logs = []
        self._parse_logs()

    def _parse_logs(self):
        """Parse structured logs."""
        for log_line in self.logs:
            try:
                log_entry = json.loads(log_line)
                self.parsed_logs.append(log_entry)
            except json.JSONDecodeError:
                # Handle non-JSON logs
                continue

    def find_error_patterns(self) -> Dict:
        """Find common error patterns."""
        error_logs = [log for log in self.parsed_logs if log.get("level") == "ERROR"]

        # Group by error message patterns
        error_patterns = defaultdict(list)
        for error_log in error_logs:
            message = error_log.get("message", "")

            # Extract patterns (remove dynamic parts)
            pattern = re.sub(r"\d+", "N", message)
            pattern = re.sub(r"[a-f0-9-]{36}", "UUID", pattern)
            pattern = re.sub(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "TIMESTAMP", pattern
            )

            error_patterns[pattern].append(error_log)

        return {
            pattern: {
                "count": len(occurrences),
                "first_seen": min(log["timestamp"] for log in occurrences),
                "last_seen": max(log["timestamp"] for log in occurrences),
                "sample_log": occurrences[0],
            }
            for pattern, occurrences in error_patterns.items()
        }

    def analyze_performance_degradation(self) -> Dict:
        """Analyze performance degradation patterns."""
        # Extract response times
        response_times = []
        for log in self.parsed_logs:
            if "duration_ms" in log:
                response_times.append(
                    {
                        "timestamp": log["timestamp"],
                        "duration": log["duration_ms"],
                        "endpoint": log.get("endpoint"),
                    }
                )

        if not response_times:
            return {}

        # Group by time buckets
        time_buckets = defaultdict(list)
        for rt in response_times:
            timestamp = datetime.fromisoformat(rt["timestamp"])
            bucket = timestamp.replace(
                minute=timestamp.minute // 5 * 5, second=0, microsecond=0
            )
            time_buckets[bucket].append(rt["duration"])

        # Calculate averages per bucket
        bucket_averages = {
            bucket: sum(durations) / len(durations)
            for bucket, durations in time_buckets.items()
        }

        # Find degradation periods
        degradation_periods = []
        baseline = sum(bucket_averages.values()) / len(bucket_averages)

        for bucket, avg_duration in bucket_averages.items():
            if avg_duration > baseline * 2:  # 100% slower than baseline
                degradation_periods.append(
                    {
                        "time": bucket,
                        "avg_duration": avg_duration,
                        "degradation_factor": avg_duration / baseline,
                    }
                )

        return {
            "baseline_ms": baseline,
            "degradation_periods": degradation_periods,
            "total_degraded_periods": len(degradation_periods),
        }

    def find_user_impact(self) -> Dict:
        """Analyze user impact from logs."""
        user_errors = defaultdict(int)
        user_requests = defaultdict(int)

        for log in self.parsed_logs:
            user_id = log.get("user_id")
            if user_id:
                user_requests[user_id] += 1
                if log.get("level") == "ERROR":
                    user_errors[user_id] += 1

        # Calculate error rates per user
        user_error_rates = {
            user_id: user_errors[user_id] / user_requests[user_id]
            for user_id in user_requests
            if user_requests[user_id] > 0
        }

        # Find users with high error rates
        affected_users = {
            user_id: {
                "error_rate": error_rate,
                "total_requests": user_requests[user_id],
                "total_errors": user_errors[user_id],
            }
            for user_id, error_rate in user_error_rates.items()
            if error_rate > 0.1  # More than 10% error rate
        }

        return {
            "total_users": len(user_requests),
            "affected_users": len(affected_users),
            "affected_user_details": affected_users,
            "overall_error_rate": sum(user_errors.values())
            / sum(user_requests.values()),
        }
```

### Automated Diagnosis

```python
# monitoring/diagnosis/auto_diagnosis.py
from typing import Dict, List
import asyncio


class AutoDiagnosisSystem:
    """Automated diagnosis system for common issues."""

    def __init__(self, metrics_client, log_analyzer, trace_analyzer):
        self.metrics = metrics_client
        self.logs = log_analyzer
        self.traces = trace_analyzer

        self.diagnosis_rules = [
            self._diagnose_high_latency,
            self._diagnose_high_error_rate,
            self._diagnose_memory_issues,
            self._diagnose_database_issues,
            self._diagnose_queue_backlog,
        ]

    async def run_diagnosis(self) -> Dict:
        """Run all diagnosis rules."""
        diagnosis_results = []

        for rule in self.diagnosis_rules:
            try:
                result = await rule()
                if result:
                    diagnosis_results.append(result)
            except Exception as e:
                diagnosis_results.append(
                    {"rule": rule.__name__, "error": str(e), "severity": "error"}
                )

        return {
            "timestamp": time.time(),
            "issues_found": len(diagnosis_results),
            "diagnoses": diagnosis_results,
        }

    async def _diagnose_high_latency(self) -> Dict:
        """Diagnose high latency issues."""
        # Get 95th percentile response time
        p95_latency = await self.metrics.query(
            "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        )

        if p95_latency > 1.0:  # Greater than 1 second
            # Get breakdown by endpoint
            endpoint_latency = await self.metrics.query(
                "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (endpoint)"
            )

            # Check database query times
            db_latency = await self.metrics.query(
                "histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m]))"
            )

            # Analyze traces for bottlenecks
            slow_traces = await self.traces.get_slow_traces(threshold=1.0, limit=10)

            return {
                "issue": "high_latency",
                "severity": "warning" if p95_latency < 2.0 else "critical",
                "description": f"95th percentile latency is {p95_latency:.2f}s",
                "metrics": {
                    "p95_latency": p95_latency,
                    "endpoint_breakdown": endpoint_latency,
                    "database_latency": db_latency,
                },
                "traces": slow_traces,
                "recommendations": [
                    "Check database query performance",
                    "Review slow endpoints for optimization",
                    "Consider adding caching",
                    "Scale horizontally if needed",
                ],
            }

        return None

    async def _diagnose_high_error_rate(self) -> Dict:
        """Diagnose high error rate issues."""
        error_rate = await self.metrics.query(
            'rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])'
        )

        if error_rate > 0.05:  # More than 5% error rate
            # Get error breakdown
            error_breakdown = await self.metrics.query(
                'rate(http_requests_total{status_code=~"5.."}[5m]) by (status_code, endpoint)'
            )

            # Analyze error logs
            recent_errors = await self.logs.get_recent_errors(hours=1)
            error_patterns = self.logs.find_error_patterns()

            return {
                "issue": "high_error_rate",
                "severity": "critical" if error_rate > 0.1 else "warning",
                "description": f"Error rate is {error_rate:.2%}",
                "metrics": {
                    "error_rate": error_rate,
                    "error_breakdown": error_breakdown,
                },
                "log_analysis": {
                    "recent_errors": recent_errors[:10],  # Top 10 recent errors
                    "error_patterns": error_patterns,
                },
                "recommendations": [
                    "Check application logs for root cause",
                    "Verify database connectivity",
                    "Check external service dependencies",
                    "Review recent deployments",
                ],
            }

        return None

    async def _diagnose_memory_issues(self) -> Dict:
        """Diagnose memory-related issues."""
        memory_usage = await self.metrics.query(
            "memory_usage_bytes / 1024 / 1024 / 1024"
        )  # GB

        if memory_usage > 7.0:  # More than 7GB usage
            # Get memory usage trend
            memory_trend = await self.metrics.query("rate(memory_usage_bytes[10m])")

            # Check for memory leaks
            gc_frequency = await self.metrics.query("rate(gc_collections_total[10m])")

            return {
                "issue": "memory_pressure",
                "severity": "critical" if memory_usage > 8.0 else "warning",
                "description": f"Memory usage is {memory_usage:.1f}GB",
                "metrics": {
                    "current_usage_gb": memory_usage,
                    "memory_trend": memory_trend,
                    "gc_frequency": gc_frequency,
                },
                "recommendations": [
                    "Check for memory leaks in application",
                    "Review large object allocations",
                    "Consider increasing memory limits",
                    "Analyze heap dumps if available",
                ],
            }

        return None
```

For more detailed monitoring setup and troubleshooting guides, see the
[Performance Guide](performance.md) and [Development Guide](../development/development-guide.md).
