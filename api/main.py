"""Main API application module."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import make_asgi_app
from strawberry.fastapi import GraphQLRouter

from .config import get_settings
from .database import close_db, init_db
from .endpoints import auth, catalog, health, media, search
from .graphql.schema import schema
from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .utils.cache import close_cache, init_cache
from .utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    logger.info("🚀 Starting Apollonia API...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Initialize cache
    await init_cache()
    logger.info("✅ Cache initialized")

    yield

    # Cleanup
    logger.info("🛑 Shutting down Apollonia API...")
    await close_cache()
    await close_db()
    logger.info("👋 Goodbye!")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    if settings.enable_metrics:
        app.add_middleware(MetricsMiddleware)

    # Add routes
    app.include_router(health.router, tags=["health"])
    app.include_router(
        auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"]
    )
    app.include_router(
        catalog.router, prefix=f"{settings.api_v1_prefix}/catalog", tags=["catalog"]
    )
    app.include_router(
        media.router, prefix=f"{settings.api_v1_prefix}/media", tags=["media"]
    )
    app.include_router(
        search.router, prefix=f"{settings.api_v1_prefix}/search", tags=["search"]
    )

    # Add GraphQL
    graphql_app = GraphQLRouter(
        schema,
        path=settings.graphql_path,
        graphiql=settings.graphql_playground,
    )
    app.include_router(graphql_app, prefix=settings.graphql_path, tags=["graphql"])

    # Add metrics endpoint
    if settings.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Add startup message
    @app.on_event("startup")
    async def startup_message() -> None:
        logger.info(
            "🎉 Apollonia API is ready! Docs at: http://localhost:8000%s/docs",
            settings.api_v1_prefix,
        )

    return app


# Create app instance
app = create_app()
