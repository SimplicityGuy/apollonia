"""API configuration module."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API settings configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "Apollonia API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API Settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://apollonia:apollonia@localhost/apollonia"
    db_pool_size: int = 20
    db_pool_max_overflow: int = 0

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600  # 1 hour

    # Authentication
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # File Storage
    upload_dir: str = "/tmp/apollonia/uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # GraphQL
    graphql_path: str = "/graphql"
    graphql_playground: bool = True

    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
