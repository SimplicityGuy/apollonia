"""End-to-end tests for the complete Apollonia system using Docker."""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests
from neo4j import GraphDatabase


class TestDockerE2E:
    """End-to-end tests for the complete system running in Docker."""

    @pytest.fixture(scope="class")
    def docker_compose_up(self):
        """Start all services using docker-compose."""
        project_root = Path(__file__).parent.parent.parent

        # Check if we should skip Docker setup
        if os.getenv("E2E_SKIP_DOCKER"):
            yield
            return

        # Start services
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=project_root,
            check=True,
        )

        # Wait for services to be ready
        self._wait_for_services()

        yield

        # Cleanup
        subprocess.run(
            ["docker-compose", "down", "-v"],
            cwd=project_root,
            check=True,
        )

    def _wait_for_services(self, timeout=60):
        """Wait for all services to be ready."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check RabbitMQ
                requests.get(
                    "http://localhost:15672/api/health/checks/alarms",
                    auth=("guest", "guest"),
                    timeout=5,
                )

                # Check Neo4j
                driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
                with driver.session() as session:
                    session.run("RETURN 1")
                driver.close()

                # If we get here, services are ready
                return

            except Exception:
                time.sleep(2)

        pytest.fail("Services did not become ready in time")

    @pytest.mark.docker
    @pytest.mark.slow
    def test_complete_file_processing_pipeline(self, docker_compose_up):  # noqa: ARG002
        """Test the complete pipeline from file creation to Neo4j storage."""
        # Create a test file in the data directory
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        test_file = data_dir / "docker_e2e_test.txt"
        test_file.write_text("Docker E2E test content")

        # Wait for file to be processed
        time.sleep(10)

        # Check Neo4j for the file
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'docker_e2e_test.txt' RETURN f"
                )
                record = result.single()

                assert record is not None, "File not found in Neo4j"
                file_node = record["f"]
                assert file_node["size"] == len("Docker E2E test content")
                assert "sha256" in file_node
                assert "xxh128" in file_node

        finally:
            driver.close()
            # Cleanup
            test_file.unlink()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_rabbitmq_message_flow(self, docker_compose_up):  # noqa: ARG002
        """Test that messages flow through RabbitMQ correctly."""
        import pika

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                "localhost", 5672, credentials=pika.PlainCredentials("guest", "guest")
            )
        )
        channel = connection.channel()

        # Check exchange exists
        try:
            channel.exchange_declare(exchange="apollonia", exchange_type="fanout", passive=True)
        except Exception as e:
            pytest.fail(f"Exchange 'apollonia' does not exist: {e}")

        # Check queue exists and has expected bindings
        queue_info = channel.queue_declare(queue="apollonia-populator", passive=True)
        assert queue_info.method.consumer_count >= 0  # Queue exists

        connection.close()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_service_health_endpoints(self, docker_compose_up):  # noqa: ARG002
        """Test that all services have working health endpoints."""
        # RabbitMQ Management API
        response = requests.get(
            "http://localhost:15672/api/health/checks/alarms", auth=("guest", "guest"), timeout=5
        )
        assert response.status_code == 200

        # Neo4j health check
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        try:
            with driver.session() as session:
                result = session.run("RETURN 1 as health")
                record = result.single()
                assert record["health"] == 1
        finally:
            driver.close()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_multiple_file_processing(self, docker_compose_up):  # noqa: ARG002
        """Test processing multiple files concurrently."""
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        # Create multiple test files
        test_files = []
        for i in range(5):
            test_file = data_dir / f"docker_test_{i}.txt"
            test_file.write_text(f"Test content {i}")
            test_files.append(test_file)

        # Wait for processing
        time.sleep(15)

        # Check all files in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'docker_test_' RETURN count(f) as count"
                )
                record = result.single()
                assert record["count"] == 5, f"Expected 5 files, found {record['count']}"

        finally:
            driver.close()
            # Cleanup
            for test_file in test_files:
                test_file.unlink()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_neighbor_file_relationships_docker(self, docker_compose_up):  # noqa: ARG002
        """Test neighbor file relationships in Docker environment."""
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        # Create related files
        files = [
            data_dir / "movie.mp4",
            data_dir / "movie.srt",
            data_dir / "movie.nfo",
        ]

        for file in files:
            file.write_text(f"Content for {file.name}")

        # Wait for processing
        time.sleep(15)

        # Check relationships in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

        try:
            with driver.session() as session:
                # Check neighbor relationships
                result = session.run(
                    """
                    MATCH (f:File)-[:NEIGHBOR]->(n:File)
                    WHERE f.path CONTAINS 'movie.mp4'
                    RETURN n.path as neighbor_path
                    """
                )
                neighbors = [record["neighbor_path"] for record in result]

                assert any("movie.srt" in path for path in neighbors)
                assert any("movie.nfo" in path for path in neighbors)

        finally:
            driver.close()
            # Cleanup
            for file in files:
                file.unlink()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_service_restart_resilience(self, docker_compose_up):  # noqa: ARG002
        """Test that system recovers from service restarts."""
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        # Create initial file
        test_file1 = data_dir / "before_restart.txt"
        test_file1.write_text("Before restart")

        # Wait for processing
        time.sleep(10)

        # Restart populator service
        subprocess.run(["docker-compose", "restart", "populator"], check=True)

        # Wait for service to come back up
        time.sleep(10)

        # Create file after restart
        test_file2 = data_dir / "after_restart.txt"
        test_file2.write_text("After restart")

        # Wait for processing
        time.sleep(10)

        # Check both files in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

        try:
            with driver.session() as session:
                # Check first file
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'before_restart.txt' RETURN f"
                )
                assert result.single() is not None

                # Check second file
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'after_restart.txt' RETURN f"
                )
                assert result.single() is not None

        finally:
            driver.close()
            # Cleanup
            test_file1.unlink()
            test_file2.unlink()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_volume_persistence(self, docker_compose_up):  # noqa: ARG002
        """Test that data persists across container restarts."""
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        # Create test file
        test_file = data_dir / "persistence_test.txt"
        test_file.write_text("Persistence test content")

        # Wait for processing
        time.sleep(10)

        # Check file in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'persistence_test.txt' "
                    "RETURN f.sha256 as hash"
                )
                record = result.single()
                original_hash = record["hash"]

            # Restart all services
            subprocess.run(["docker-compose", "restart"], check=True)

            # Wait for services to come back
            self._wait_for_services()

            # Check file still exists with same hash
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'persistence_test.txt' "
                    "RETURN f.sha256 as hash"
                )
                record = result.single()
                assert record is not None, "File not found after restart"
                assert record["hash"] == original_hash, "File hash changed after restart"

        finally:
            driver.close()
            # Cleanup
            test_file.unlink()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_logs_availability(self, docker_compose_up):  # noqa: ARG002
        """Test that service logs are available and contain expected entries."""
        # Get logs from each service
        services = ["rabbitmq", "neo4j", "ingestor", "populator"]

        for service in services:
            result = subprocess.run(
                ["docker-compose", "logs", "--tail=50", service],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Failed to get logs for {service}"
            assert len(result.stdout) > 0, f"No logs found for {service}"

            # Service-specific log checks
            if service == "ingestor":
                assert "apollonia" in result.stdout.lower()
                assert "ingestor" in result.stdout.lower()
            elif service == "populator":
                assert "apollonia" in result.stdout.lower()
                assert "populator" in result.stdout.lower()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_resource_usage_monitoring(self, docker_compose_up):  # noqa: ARG002
        """Test that containers are not using excessive resources."""
        # Get container stats
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Parse stats (each line is a JSON object)
        import json

        for line in result.stdout.strip().split("\n"):
            if line:
                stats = json.loads(line)
                container_name = stats.get("Name", "")

                # Check if it's one of our containers
                if any(service in container_name for service in ["apollonia", "rabbitmq", "neo4j"]):
                    # Parse CPU percentage (remove % sign)
                    cpu_percent = float(stats.get("CPUPerc", "0%").rstrip("%"))

                    # Check CPU usage (should be reasonable during idle)
                    assert cpu_percent < 80.0, (
                        f"{container_name} using too much CPU: {cpu_percent}%"
                    )

                    # Could also check memory usage if needed
