"""End-to-end tests for the complete Apollonia system using Docker."""

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests
from neo4j import GraphDatabase


class TestDockerE2E:
    """End-to-end tests for the complete system running in Docker."""

    @staticmethod
    def create_file_in_container(filename: str, content: str) -> None:
        """Create a file inside the ingestor container to ensure watchdog detects it."""
        subprocess.run(
            [
                "docker",
                "exec",
                "--user",
                "apollonia",
                "apollonia-ingestor",
                "sh",
                "-c",
                f"printf '%s' '{content}' > /data/{filename}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def remove_file_from_container(filename: str) -> None:
        """Remove a file from inside the ingestor container."""
        subprocess.run(
            [
                "docker",
                "exec",
                "--user",
                "apollonia",
                "apollonia-ingestor",
                "rm",
                "-f",
                f"/data/{filename}",
            ],
            capture_output=True,
        )

    @pytest.fixture(scope="class")
    def docker_compose_up(self) -> Iterator[None]:
        """Start all services with enhanced readiness verification."""
        project_root = Path(__file__).parent.parent.parent

        # Check if we should skip Docker setup
        if os.getenv("E2E_SKIP_DOCKER"):
            yield
            return

        try:
            # Ensure data directory exists
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)

            # Clean up any existing containers first
            print("🧹 Cleaning up any existing containers...")
            subprocess.run(
                ["docker-compose", "--profile", "legacy", "down", "-v", "--remove-orphans"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Start with proper error handling, including legacy profile for ingestor
            print("🚀 Starting Docker services...")
            result = subprocess.run(
                ["docker-compose", "--profile", "legacy", "up", "-d"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"❌ Docker compose failed with return code {result.returncode}")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
                pytest.fail(f"Docker compose failed to start: {result.stderr}")

            # Show running containers
            print("📦 Running containers:")
            subprocess.run(["docker-compose", "--profile", "legacy", "ps"], cwd=project_root)

            # Enhanced service readiness with retries
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(
                        f"\n🔄 Attempt {attempt + 1}/{max_attempts} to verify service readiness..."
                    )
                    self._wait_for_services(timeout=180)
                    print("✅ All services are ready!")
                    break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        # On final failure, show logs to help debug
                        print("\n❌ Services failed to start. Showing logs:")
                        subprocess.run(
                            ["docker-compose", "logs", "--tail=50"],
                            cwd=project_root,
                        )
                        raise
                    print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                    print("⏳ Waiting 30 seconds before retry...")
                    time.sleep(30)

            yield

        finally:
            # Enhanced cleanup
            print("\n🧹 Cleaning up Docker services...")
            result = subprocess.run(
                ["docker-compose", "--profile", "legacy", "down", "-v", "--remove-orphans"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                print(f"⚠️ Cleanup failed: {result.stderr}")
            else:
                print("✅ Cleanup completed successfully")

    def _wait_for_services(self, timeout: int = 120) -> None:
        """Wait for all services to be ready with exponential backoff."""
        import pika
        import psycopg2
        import redis

        services_ready = {"rabbitmq": False, "neo4j": False, "postgres": False, "redis": False}

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout and not all(services_ready.values()):
            attempt += 1
            backoff_time = min(2 ** (attempt // 3), 10)  # Exponential backoff, max 10s

            # Check RabbitMQ with exchange validation
            if not services_ready["rabbitmq"]:
                try:
                    # First check management API
                    response = requests.get(
                        "http://localhost:15672/api/exchanges/%2F/apollonia",
                        auth=("apollonia", "apollonia"),
                        timeout=5,
                    )
                    if response.status_code == 200:
                        # Then verify AMQP connection
                        connection = pika.BlockingConnection(
                            pika.ConnectionParameters(
                                "localhost",
                                5672,
                                credentials=pika.PlainCredentials("apollonia", "apollonia"),
                            )
                        )
                        connection.close()
                        services_ready["rabbitmq"] = True
                        print("✅ RabbitMQ is ready")
                except Exception as e:
                    if attempt % 5 == 0:  # Log every 5th attempt
                        print(f"⏳ RabbitMQ not ready: {e}")

            # Check Neo4j with actual query
            if not services_ready["neo4j"]:
                try:
                    driver = GraphDatabase.driver(
                        "bolt://localhost:7687", auth=("neo4j", "apollonia")
                    )
                    with driver.session() as session:
                        result = session.run("RETURN 1 as test")
                        result.consume()  # Ensure query completes
                    driver.close()
                    services_ready["neo4j"] = True
                    print("✅ Neo4j is ready")
                except Exception as e:
                    if attempt % 5 == 0:
                        print(f"⏳ Neo4j not ready: {e}")

            # Check PostgreSQL
            if not services_ready["postgres"]:
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        user="apollonia",
                        password="apollonia",  # noqa: S106
                        database="apollonia",
                        connect_timeout=5,
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    services_ready["postgres"] = True
                    print("✅ PostgreSQL is ready")
                except Exception as e:
                    if attempt % 5 == 0:
                        print(f"⏳ PostgreSQL not ready: {e}")

            # Check Redis
            if not services_ready["redis"]:
                try:
                    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                    r.ping()
                    services_ready["redis"] = True
                    print("✅ Redis is ready")
                except Exception as e:
                    if attempt % 5 == 0:
                        print(f"⏳ Redis not ready: {e}")

            if not all(services_ready.values()):
                time.sleep(backoff_time)

        if not all(services_ready.values()):
            failed = [k for k, v in services_ready.items() if not v]
            pytest.fail(f"Services failed to start within {timeout}s: {failed}")

        # Additional warm-up period for service stabilization
        print("⏳ Warming up services...")
        time.sleep(10)

    @pytest.mark.docker
    @pytest.mark.slow
    def test_complete_file_processing_pipeline(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test the complete pipeline from file creation to Neo4j storage."""
        # Create a test file inside the container to ensure watchdog detects it
        self.create_file_in_container("docker_e2e_test.txt", "Docker E2E test content")

        # Wait for file to be processed
        time.sleep(10)

        # Check Neo4j for the file
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

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
            self.remove_file_from_container("docker_e2e_test.txt")

    @pytest.mark.docker
    @pytest.mark.slow
    def test_rabbitmq_message_flow(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test that messages flow through RabbitMQ correctly."""
        import pika

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                "localhost", 5672, credentials=pika.PlainCredentials("apollonia", "apollonia")
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
    def test_service_health_endpoints(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test that all services have working health endpoints."""
        # RabbitMQ Management API
        response = requests.get(
            "http://localhost:15672/api/health/checks/alarms",
            auth=("apollonia", "apollonia"),
            timeout=5,
        )
        assert response.status_code == 200

        # Neo4j health check
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))
        try:
            with driver.session() as session:
                result = session.run("RETURN 1 as health")
                record = result.single()
                assert record is not None and record["health"] == 1
        finally:
            driver.close()

    @pytest.mark.docker
    @pytest.mark.slow
    def test_multiple_file_processing(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test processing multiple files concurrently."""
        # Create multiple test files inside the container
        for i in range(5):
            self.create_file_in_container(f"docker_test_{i}.txt", f"Test content {i}")

        # Wait for processing
        time.sleep(15)

        # Check all files in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'docker_test_' RETURN count(f) as count"
                )
                record = result.single()
                assert record is not None and record["count"] == 5, (
                    f"Expected 5 files, found {record['count'] if record else 'None'}"
                )

        finally:
            driver.close()
            # Cleanup
            for i in range(5):
                self.remove_file_from_container(f"docker_test_{i}.txt")

    @pytest.mark.docker
    @pytest.mark.slow
    def test_neighbor_file_relationships_docker(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test neighbor file relationships in Docker environment."""
        # Create all related files at once to ensure they exist before processing
        subprocess.run(
            [
                "docker",
                "exec",
                "--user",
                "apollonia",
                "apollonia-ingestor",
                "sh",
                "-c",
                "printf 'Content for movie.mp4' > /data/movie.mp4 && "
                "printf 'Content for movie.srt' > /data/movie.srt && "
                "printf 'Content for movie.nfo' > /data/movie.nfo",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Wait for processing
        time.sleep(15)

        # Check relationships in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

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
            for filename in ["movie.mp4", "movie.srt", "movie.nfo"]:
                self.remove_file_from_container(filename)

    @pytest.mark.docker
    @pytest.mark.slow
    def test_service_restart_resilience(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test that system recovers from service restarts."""
        # Create initial file inside the container
        self.create_file_in_container("before_restart.txt", "Before restart")

        # Wait for processing
        time.sleep(10)

        # Restart populator service
        subprocess.run(
            ["docker-compose", "--profile", "legacy", "restart", "populator"], check=True
        )

        # Wait for service to come back up
        time.sleep(10)

        # Create file after restart
        self.create_file_in_container("after_restart.txt", "After restart")

        # Wait for processing
        time.sleep(10)

        # Check both files in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

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
            self.remove_file_from_container("before_restart.txt")
            self.remove_file_from_container("after_restart.txt")

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_volume_persistence(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test that data persists across container restarts."""
        # Create test file inside the container
        self.create_file_in_container("persistence_test.txt", "Persistence test content")

        # Wait for processing
        time.sleep(10)

        # Check file in Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (f:File) WHERE f.path CONTAINS 'persistence_test.txt' "
                    "RETURN f.sha256 as hash"
                )
                record = result.single()
                assert record is not None
                original_hash = record["hash"]

            # Close the driver before restart
            driver.close()

            # Restart all services
            subprocess.run(["docker-compose", "--profile", "legacy", "restart"], check=True)

            # Wait for services to come back
            self._wait_for_services()

            # Create new driver after restart
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

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
            self.remove_file_from_container("persistence_test.txt")

    @pytest.mark.docker
    @pytest.mark.slow
    def test_docker_logs_availability(self, docker_compose_up: None) -> None:  # noqa: ARG002
        """Test that service logs are available and contain expected entries."""
        # Get logs from each service
        services = ["rabbitmq", "neo4j", "ingestor", "populator"]

        for service in services:
            result = subprocess.run(
                ["docker-compose", "--profile", "legacy", "logs", "--tail=50", service],
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
    def test_resource_usage_monitoring(self, docker_compose_up: None) -> None:  # noqa: ARG002
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
                    # Neo4j can use more CPU during startup and indexing
                    cpu_threshold = 95.0 if "neo4j" in container_name else 80.0
                    assert cpu_percent < cpu_threshold, (
                        f"{container_name} using too much CPU: {cpu_percent}%"
                    )

                    # Could also check memory usage if needed
