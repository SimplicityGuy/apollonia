"""Performance benchmarks for Neo4j graph operations."""

import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

import pytest


class MockNeo4jDriver:
    """Mock Neo4j driver for benchmarking without actual database."""

    async def execute_query(self, query: str, parameters: dict[str, Any]) -> Any:
        """Simulate query execution with minimal overhead."""
        await asyncio.sleep(0.001)  # Simulate network latency
        return {"nodes_created": 1, "relationships_created": len(parameters.get("neighbors", []))}

    async def close(self) -> None:
        """Close mock driver."""
        pass


def create_file_node_data(num_neighbors: int = 10) -> dict[str, Any]:
    """Create sample file node data."""
    return {
        "path": "/data/test/sample_file.mp4",
        "name": "sample_file.mp4",
        "sha256": "a" * 64,
        "xxh128": "b" * 32,
        "modified_time": datetime.now(UTC),
        "accessed_time": datetime.now(UTC),
        "changed_time": datetime.now(UTC),
        "neighbors": [f"neighbor_{i}.txt" for i in range(num_neighbors)],
    }


async def insert_single_node(driver: MockNeo4jDriver, data: dict[str, Any]) -> Any:
    """Insert a single file node."""
    query = """
    CREATE (f:File {
        path: $path,
        name: $name,
        sha256: $sha256,
        xxh128: $xxh128,
        modified_time: $modified_time,
        accessed_time: $accessed_time,
        changed_time: $changed_time
    })
    RETURN f
    """
    return await driver.execute_query(query, data)


async def insert_node_with_relationships(driver: MockNeo4jDriver, data: dict[str, Any]) -> Any:
    """Insert a file node with neighbor relationships."""
    query = """
    CREATE (f:File {
        path: $path,
        name: $name,
        sha256: $sha256,
        xxh128: $xxh128,
        modified_time: $modified_time,
        accessed_time: $accessed_time,
        changed_time: $changed_time
    })
    WITH f
    UNWIND $neighbors AS neighbor
    MERGE (n:File {name: neighbor})
    CREATE (f)-[:NEIGHBOR]->(n)
    RETURN f
    """
    return await driver.execute_query(query, data)


async def batch_insert_nodes(driver: MockNeo4jDriver, nodes: list[dict[str, Any]]) -> Any:
    """Batch insert multiple file nodes."""
    query = """
    UNWIND $nodes AS node
    CREATE (f:File {
        path: node.path,
        name: node.name,
        sha256: node.sha256,
        xxh128: node.xxh128,
        modified_time: node.modified_time,
        accessed_time: node.accessed_time,
        changed_time: node.changed_time
    })
    RETURN count(f) as nodes_created
    """
    return await driver.execute_query(query, {"nodes": nodes})


@pytest.fixture
def mock_driver() -> Generator[MockNeo4jDriver, None, None]:
    """Create mock Neo4j driver."""
    driver = MockNeo4jDriver()
    yield driver
    asyncio.run(driver.close())


class TestNeo4jPerformance:
    """Benchmark tests for Neo4j operations."""

    def test_single_node_insert(self, benchmark: Any, mock_driver: MockNeo4jDriver) -> None:
        """Benchmark single node insertion."""
        data = create_file_node_data(num_neighbors=0)

        def insert() -> Any:
            return asyncio.run(insert_single_node(mock_driver, data))

        result = benchmark(insert)
        assert result["nodes_created"] == 1

    def test_node_with_few_relationships(
        self, benchmark: Any, mock_driver: MockNeo4jDriver
    ) -> None:
        """Benchmark node insertion with few relationships."""
        data = create_file_node_data(num_neighbors=5)

        def insert() -> Any:
            return asyncio.run(insert_node_with_relationships(mock_driver, data))

        result = benchmark(insert)
        assert result["relationships_created"] == 5

    def test_node_with_many_relationships(
        self, benchmark: Any, mock_driver: MockNeo4jDriver
    ) -> None:
        """Benchmark node insertion with many relationships."""
        data = create_file_node_data(num_neighbors=50)

        def insert() -> Any:
            return asyncio.run(insert_node_with_relationships(mock_driver, data))

        result = benchmark(insert)
        assert result["relationships_created"] == 50

    def test_batch_insert_small(self, benchmark: Any, mock_driver: MockNeo4jDriver) -> None:
        """Benchmark small batch insertion."""
        nodes = [create_file_node_data(num_neighbors=0) for _ in range(10)]

        def insert() -> Any:
            return asyncio.run(batch_insert_nodes(mock_driver, nodes))

        result = benchmark(insert)
        assert result is not None

    def test_batch_insert_large(self, benchmark: Any, mock_driver: MockNeo4jDriver) -> None:
        """Benchmark large batch insertion."""
        nodes = [create_file_node_data(num_neighbors=0) for _ in range(100)]

        def insert() -> Any:
            return asyncio.run(batch_insert_nodes(mock_driver, nodes))

        result = benchmark(insert)
        assert result is not None
