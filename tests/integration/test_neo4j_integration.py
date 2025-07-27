"""Integration tests for Neo4j functionality."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

import pytest
from neo4j import AsyncGraphDatabase, GraphDatabase

pytestmark = pytest.mark.integration


@pytest.fixture
def neo4j_config() -> dict[str, str]:
    """Get Neo4j configuration from environment."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "apollonia"),
    }


@pytest.fixture
def skip_if_no_neo4j(neo4j_config: dict[str, str]) -> None:
    """Skip test if Neo4j is not available."""
    try:
        driver = GraphDatabase.driver(
            neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
        )
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
    except Exception:
        pytest.skip("Neo4j server not available")


@pytest.fixture
async def neo4j_driver(neo4j_config: dict[str, str], _skip_if_no_neo4j: None) -> AsyncIterator[Any]:
    """Create async Neo4j driver."""
    driver = AsyncGraphDatabase.driver(
        neo4j_config["uri"], auth=(neo4j_config["user"], neo4j_config["password"])
    )
    yield driver
    await driver.close()


@pytest.fixture
async def clean_database(neo4j_driver: Any) -> AsyncIterator[None]:
    """Clean test data from database."""
    async with neo4j_driver.session() as session:
        # Delete test nodes
        await session.run("MATCH (f:File) WHERE f.path STARTS WITH '/test/' DELETE f")
    yield
    # Cleanup after test
    async with neo4j_driver.session() as session:
        await session.run("MATCH (f:File) WHERE f.path STARTS WITH '/test/' DELETE f")


class TestNeo4jIntegration:
    """Test Neo4j integration for populator service."""

    @pytest.mark.asyncio
    async def test_connection(self, neo4j_driver: Any) -> None:
        """Test basic Neo4j connection."""
        async with neo4j_driver.session() as session:
            result = await session.run("RETURN 1 AS value")
            record = await result.single()
            assert record["value"] == 1

    @pytest.mark.asyncio
    async def test_create_file_node(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test creating a file node."""
        file_data = {
            "file_path": "/test/example.txt",
            "sha256_hash": "abc123",
            "xxh128_hash": "def456",
            "size": 1024,
            "modified_time": "2024-01-01T10:00:00+00:00",
            "accessed_time": "2024-01-01T11:00:00+00:00",
            "changed_time": "2024-01-01T09:00:00+00:00",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "event_type": "IN_CREATE",
        }

        async with neo4j_driver.session() as session:
            # Create node
            query = """
            MERGE (f:File {path: $file_path})
            SET f.sha256 = $sha256_hash,
                f.xxh128 = $xxh128_hash,
                f.size = $size,
                f.modified = datetime($modified_time),
                f.accessed = datetime($accessed_time),
                f.changed = datetime($changed_time),
                f.discovered = datetime($timestamp),
                f.event_type = $event_type
            RETURN f
            """

            result = await session.run(query, **file_data)
            record = await result.single()

            assert record is not None
            node = record["f"]
            assert node["path"] == file_data["file_path"]
            assert node["sha256"] == file_data["sha256_hash"]
            assert node["size"] == file_data["size"]

    @pytest.mark.asyncio
    async def test_update_existing_node(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test updating an existing file node."""
        file_path = "/test/update.txt"

        async with neo4j_driver.session() as session:
            # Create initial node
            await session.run(
                "CREATE (f:File {path: $path, sha256: $hash, size: $size})",
                path=file_path,
                hash="old_hash",
                size=500,
            )

            # Update node
            update_data = {
                "file_path": file_path,
                "sha256_hash": "new_hash",
                "size": 1000,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            query = """
            MERGE (f:File {path: $file_path})
            SET f.sha256 = $sha256_hash,
                f.size = $size,
                f.discovered = datetime($timestamp)
            RETURN f
            """

            result = await session.run(query, **update_data)
            record = await result.single()

            # Verify update
            node = record["f"]
            assert node["sha256"] == "new_hash"
            assert node["size"] == 1000

    @pytest.mark.asyncio
    async def test_neighbor_relationships(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test creating neighbor relationships between files."""
        async with neo4j_driver.session() as session:
            # Create main file
            main_file = "/test/main.mp3"
            await session.run("CREATE (f:File {path: $path})", path=main_file)

            # Create neighbors and relationships
            neighbors = ["/test/main.txt", "/test/main.log", "/test/tracklist.txt"]

            for neighbor_path in neighbors:
                await session.run(
                    """
                    MERGE (f1:File {path: $file_path})
                    MERGE (f2:File {path: $neighbor_path})
                    MERGE (f1)-[:NEIGHBOR]->(f2)
                """,
                    file_path=main_file,
                    neighbor_path=neighbor_path,
                )

            # Query neighbors
            result = await session.run(
                """
                MATCH (f:File {path: $path})-[:NEIGHBOR]->(n:File)
                RETURN n.path AS neighbor_path
                ORDER BY neighbor_path
            """,
                path=main_file,
            )

            neighbor_paths = [record["neighbor_path"] async for record in result]
            assert neighbor_paths == sorted(neighbors)

    @pytest.mark.asyncio
    async def test_find_duplicates_by_hash(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test finding duplicate files by hash."""
        test_hash = "duplicate_hash_123"

        async with neo4j_driver.session() as session:
            # Create multiple files with same hash
            files = ["/test/file1.txt", "/test/file2.txt", "/test/subfolder/file1.txt"]

            for file_path in files:
                await session.run(
                    "CREATE (f:File {path: $path, sha256: $hash})", path=file_path, hash=test_hash
                )

            # Create one with different hash
            await session.run(
                "CREATE (f:File {path: $path, sha256: $hash})",
                path="/test/different.txt",
                hash="different_hash",
            )

            # Find duplicates
            result = await session.run(
                """
                MATCH (f:File {sha256: $hash})
                RETURN f.path AS path
                ORDER BY path
            """,
                hash=test_hash,
            )

            duplicate_paths = [record["path"] async for record in result]
            assert duplicate_paths == sorted(files)

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test transaction rollback on error."""
        async with neo4j_driver.session() as session:
            try:
                async with session.begin_transaction() as tx:
                    # Create a node
                    await tx.run("CREATE (f:File {path: $path})", path="/test/rollback.txt")

                    # Force an error
                    await tx.run("INVALID CYPHER QUERY")

            except Exception:  # noqa: S110
                pass  # Expected

            # Verify node was not created
            result = await session.run(
                "MATCH (f:File {path: $path}) RETURN f", path="/test/rollback.txt"
            )
            record = await result.single()
            assert record is None

    @pytest.mark.asyncio
    async def test_performance_with_indexes(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test performance improvement with indexes."""
        async with neo4j_driver.session() as session:
            # Create index if not exists
            try:
                await session.run(
                    "CREATE INDEX file_path_index IF NOT EXISTS FOR (f:File) ON (f.path)"
                )
                await session.run(
                    "CREATE INDEX file_sha256_index IF NOT EXISTS FOR (f:File) ON (f.sha256)"
                )
            except Exception:  # noqa: S110
                pass  # Indexes might already exist

            # Create many nodes
            num_nodes = 100
            for i in range(num_nodes):
                await session.run(
                    "CREATE (f:File {path: $path, sha256: $hash})",
                    path=f"/test/perf/file_{i}.txt",
                    hash=f"hash_{i % 10}",  # 10 unique hashes
                )

            # Query with indexed field
            result = await session.run(
                "MATCH (f:File {sha256: $hash}) RETURN count(f) AS count", hash="hash_5"
            )
            record = await result.single()
            assert record["count"] == 10  # Should find 10 files with hash_5

    @pytest.mark.asyncio
    async def test_datetime_handling(self, neo4j_driver: Any, _clean_database: None) -> None:
        """Test proper datetime handling."""
        now = datetime.now(UTC)

        async with neo4j_driver.session() as session:
            # Create node with datetime
            await session.run(
                """
                CREATE (f:File {
                    path: $path,
                    discovered: datetime($timestamp)
                })
            """,
                path="/test/datetime.txt",
                timestamp=now.isoformat(),
            )

            # Query and verify
            result = await session.run(
                """
                MATCH (f:File {path: $path})
                RETURN f.discovered AS discovered
            """,
                path="/test/datetime.txt",
            )

            record = await result.single()
            # Neo4j returns datetime as neo4j.time.DateTime
            discovered = record["discovered"]
            assert discovered is not None
