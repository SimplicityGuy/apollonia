"""Test suite for API service."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test the readiness check endpoint."""
        response = client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data

    def test_liveness_check(self, client: TestClient) -> None:
        """Test the liveness check endpoint."""
        response = client.get("/liveness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestCatalogEndpoints:
    """Test catalog endpoints."""

    def test_list_media_files(self, client: TestClient) -> None:
        """Test listing media files."""
        response = client.get("/api/v1/catalog/media")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_search_media(self, client: TestClient) -> None:
        """Test searching media files."""
        response = client.get("/api/v1/catalog/search", params={"q": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
        assert data["query"] == "test"


class TestGraphQLEndpoint:
    """Test GraphQL endpoint."""

    def test_graphql_playground(self, client: TestClient) -> None:
        """Test GraphQL playground is accessible."""
        response = client.get("/graphql")
        assert response.status_code == 200

    def test_graphql_query(self, client: TestClient) -> None:
        """Test a basic GraphQL query."""
        query = """
        query {
            health {
                status
                version
            }
        }
        """
        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "health" in data["data"]


class TestMiddleware:
    """Test API middleware."""

    def test_cors_headers(self, client: TestClient) -> None:
        """Test CORS headers are properly set."""
        response = client.options("/api/v1/catalog/media")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_request_id_header(self, client: TestClient) -> None:
        """Test request ID header is added."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "x-request-id" in response.headers


class TestErrorHandling:
    """Test error handling."""

    def test_404_error(self, client: TestClient) -> None:
        """Test 404 error handling."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_validation_error(self, client: TestClient) -> None:
        """Test validation error handling."""
        response = client.get("/api/v1/catalog/media", params={"limit": "invalid"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
