#!/bin/bash
# Script to create database migrations

# Start PostgreSQL if not running
docker compose up -d postgres

# Wait for PostgreSQL to be ready
echo "🔄 Waiting for PostgreSQL to be ready..."
sleep 5

# Run migration with environment variable
export DATABASE_URL="postgresql+asyncpg://apollonia:apollonia@localhost:5432/apollonia"

# Run Alembic migration
echo "🚀 Creating migration: $1"
cd .. && uv run alembic revision --autogenerate -m "$1"
