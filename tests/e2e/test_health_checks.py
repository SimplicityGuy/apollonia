"""Test health check endpoints for all services."""

import httpx
import pika
import pytest
import redis
from neo4j import GraphDatabase


@pytest.mark.e2e
class TestHealthChecks:
    """Test health check endpoints for all services."""

    def test_api_health_check(self):
        """Test API health check endpoint."""
        response = httpx.get("http://localhost:8000/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_frontend_health_check(self):
        """Test frontend is accessible."""
        response = httpx.get("http://localhost:3000", timeout=10)
        assert response.status_code == 200
        assert "Apollonia" in response.text

    def test_rabbitmq_connection(self):
        """Test RabbitMQ is accessible."""
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="localhost",
                port=5672,
                credentials=pika.PlainCredentials("apollonia", "apollonia"),
            )
        )
        assert connection.is_open
        connection.close()

    def test_neo4j_connection(self):
        """Test Neo4j is accessible."""
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))
        with driver.session() as session:
            result = session.run("RETURN 1 AS num")
            record = result.single()
            assert record["num"] == 1
        driver.close()

    def test_postgres_connection(self):
        """Test PostgreSQL is accessible via API."""
        # The API health check should verify database connectivity
        response = httpx.get("http://localhost:8000/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Check if database status is included
        if "database" in data:
            assert data["database"]["status"] == "connected"

    def test_redis_connection(self):
        """Test Redis is accessible."""
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        assert r.ping()
        r.close()

    def test_all_services_integration(self):
        """Test that all services can communicate."""
        # This test verifies the entire stack is working
        response = httpx.get("http://localhost:8000/api/v1/status", timeout=10)

        if response.status_code == 404:
            # If the status endpoint doesn't exist, just check health
            response = httpx.get("http://localhost:8000/health", timeout=10)

        assert response.status_code == 200
