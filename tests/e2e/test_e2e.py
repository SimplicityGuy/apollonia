"""End-to-end tests for the complete Apollonia system."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING

import docker
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Create Docker client."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        pytest.skip("Docker not available")


@pytest.fixture(scope="session")
def docker_compose_project(_docker_client: docker.DockerClient) -> Iterator[str]:
    """Start docker-compose services for testing."""
    import subprocess

    project_name = "apollonia-e2e-test"
    compose_file = Path(__file__).parent.parent.parent / "docker-compose.yml"

    if not compose_file.exists():
        pytest.skip("docker-compose.yml not found")

    # Start services
    try:
        subprocess.run(
            ["docker-compose", "-p", project_name, "-f", str(compose_file), "up", "-d"],
            check=True,
            capture_output=True,
        )

        # Wait for services to be ready
        time.sleep(10)

        yield project_name

    finally:
        # Stop and remove services
        subprocess.run(
            ["docker-compose", "-p", project_name, "-f", str(compose_file), "down", "-v"],
            check=False,
            capture_output=True,
        )


class TestEndToEnd:
    """End-to-end tests for the complete system."""

    def test_docker_services_running(
        self, docker_client: docker.DockerClient, docker_compose_project: str
    ) -> None:
        """Test that all services are running."""
        containers = docker_client.containers.list()
        container_names = [c.name for c in containers]

        # Check required services
        required_services = [
            f"{docker_compose_project}_rabbitmq_1",
            f"{docker_compose_project}_neo4j_1",
            f"{docker_compose_project}_ingestor_1",
            f"{docker_compose_project}_populator_1",
        ]

        for service in required_services:
            assert any(service in name for name in container_names), f"{service} not running"

    def test_file_processing_flow(
        self, docker_client: docker.DockerClient, docker_compose_project: str
    ) -> None:
        """Test complete file processing flow."""
        # Get the data volume path
        ingestor_container = None
        for container in docker_client.containers.list():
            if "ingestor" in container.name and docker_compose_project in container.name:
                ingestor_container = container
                break

        assert ingestor_container is not None

        # Create a test file in the data directory
        test_filename = f"test_{int(time.time())}.txt"
        test_content = "End-to-end test content"

        # Execute command in container to create file
        exec_result = ingestor_container.exec_run(
            f"sh -c 'echo \"{test_content}\" > /data/{test_filename}'", user="apollonia"
        )
        assert exec_result.exit_code == 0

        # Wait for processing
        time.sleep(5)

        # Check logs to verify processing
        ingestor_logs = ingestor_container.logs(tail=50).decode()
        assert test_filename in ingestor_logs or "Published event" in ingestor_logs

        # Check populator processed the message
        populator_container = None
        for container in docker_client.containers.list():
            if "populator" in container.name and docker_compose_project in container.name:
                populator_container = container
                break

        if populator_container:
            populator_logs = populator_container.logs(tail=50).decode()
            assert "Processing file" in populator_logs or test_filename in populator_logs

    @pytest.mark.asyncio
    async def test_neo4j_data_verification(self, _docker_compose_project: str) -> None:
        """Verify data was stored in Neo4j."""
        from neo4j import AsyncGraphDatabase

        # Wait for any pending processing
        await asyncio.sleep(5)

        # Connect to Neo4j
        driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "apollonia"))

        try:
            async with driver.session() as session:
                # Count file nodes
                result = await session.run("MATCH (f:File) RETURN count(f) AS count")
                record = await result.single()

                # Should have at least one file from our test
                assert record is not None
                assert record["count"] > 0

                # Check for recent files
                result = await session.run("""
                    MATCH (f:File)
                    WHERE f.discovered > datetime() - duration('PT5M')
                    RETURN f.path AS path
                    ORDER BY f.discovered DESC
                    LIMIT 10
                """)

                recent_files = [record["path"] async for record in result]
                assert len(recent_files) > 0

        finally:
            await driver.close()

    def test_health_checks(
        self, docker_client: docker.DockerClient, docker_compose_project: str
    ) -> None:
        """Test that health checks are passing."""
        unhealthy_containers = []

        for container in docker_client.containers.list():
            if docker_compose_project in container.name:
                # Reload to get latest status
                container.reload()
                health = container.attrs.get("State", {}).get("Health", {})
                status = health.get("Status", "none")

                if status not in ["healthy", "none"]:  # "none" means no health check defined
                    unhealthy_containers.append(
                        {
                            "name": container.name,
                            "status": status,
                            "logs": health.get("Log", [])[-1] if health.get("Log") else None,
                        }
                    )

        assert len(unhealthy_containers) == 0, f"Unhealthy containers: {unhealthy_containers}"

    def test_service_restart_recovery(
        self, docker_client: docker.DockerClient, docker_compose_project: str
    ) -> None:
        """Test that services recover from restart."""
        # Find and restart the ingestor
        ingestor_container = None
        for container in docker_client.containers.list():
            if "ingestor" in container.name and docker_compose_project in container.name:
                ingestor_container = container
                break

        assert ingestor_container is not None

        # Restart the container
        ingestor_container.restart()

        # Wait for it to come back up
        time.sleep(5)

        # Verify it's running again
        ingestor_container.reload()
        assert ingestor_container.status == "running"

        # Create another test file to verify it's processing
        test_filename = f"restart_test_{int(time.time())}.txt"
        exec_result = ingestor_container.exec_run(
            f"sh -c 'echo \"Restart test\" > /data/{test_filename}'", user="apollonia"
        )
        assert exec_result.exit_code == 0

        # Wait and check logs
        time.sleep(3)
        logs = ingestor_container.logs(tail=20).decode()
        assert "Starting file monitoring" in logs  # Shows it restarted successfully
