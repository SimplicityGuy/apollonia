"""Prometheus metrics middleware."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Active HTTP requests",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for Prometheus metrics collection."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        # Increment active requests
        ACTIVE_REQUESTS.inc()

        # Start timing
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            status = response.status_code

            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status,
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            return response

        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()
