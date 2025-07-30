# Apollonia API Service

RESTful API and GraphQL service for the Apollonia media processing system.

## Overview

This service provides:

- RESTful endpoints for media catalog access
- GraphQL API for flexible queries
- Authentication and authorization
- Real-time updates via WebSocket
- Health monitoring endpoints

## Endpoints

### REST API

- `/health` - Health check endpoint
- `/readiness` - Readiness check endpoint
- `/liveness` - Liveness check endpoint
- `/api/v1/media` - Media catalog endpoints
- `/api/v1/auth` - Authentication endpoints

### GraphQL

- `/graphql` - GraphQL endpoint
- `/graphiql` - GraphQL playground (development only)

## Development

See the main project README for development setup instructions.
