"""Performance benchmarks for AMQP message processing."""

import json
from datetime import UTC, datetime
from typing import Any, cast

import orjson


def create_file_metadata(num_neighbors: int = 10) -> dict[str, Any]:
    """Create a sample file metadata message."""
    return {
        "file_path": "/data/test/sample_file.mp4",
        "event_type": "IN_CREATE",
        "sha256_hash": "a" * 64,
        "xxh128_hash": "b" * 32,
        "modified_time": datetime.now(UTC).isoformat(),
        "accessed_time": datetime.now(UTC).isoformat(),
        "changed_time": datetime.now(UTC).isoformat(),
        "neighbors": [f"neighbor_{i}.txt" for i in range(num_neighbors)],
    }


def serialize_json(data: dict[str, Any]) -> bytes:
    """Serialize data using standard json library."""
    return json.dumps(data).encode("utf-8")


def deserialize_json(data: bytes) -> dict[str, Any]:
    """Deserialize data using standard json library."""
    return cast("dict[str, Any]", json.loads(data.decode("utf-8")))


def serialize_orjson(data: dict[str, Any]) -> bytes:
    """Serialize data using orjson library."""
    return orjson.dumps(data)


def deserialize_orjson(data: bytes) -> dict[str, Any]:
    """Deserialize data using orjson library."""
    return cast("dict[str, Any]", orjson.loads(data))


class TestMessageSerializationPerformance:
    """Benchmark tests for message serialization performance."""

    def test_json_serialize_small(self, benchmark: Any) -> None:
        """Benchmark standard JSON serialization of small message."""
        data = create_file_metadata(num_neighbors=10)
        result = benchmark(serialize_json, data)
        assert isinstance(result, bytes)

    def test_orjson_serialize_small(self, benchmark: Any) -> None:
        """Benchmark orjson serialization of small message."""
        data = create_file_metadata(num_neighbors=10)
        result = benchmark(serialize_orjson, data)
        assert isinstance(result, bytes)

    def test_json_deserialize_small(self, benchmark: Any) -> None:
        """Benchmark standard JSON deserialization of small message."""
        data = serialize_json(create_file_metadata(num_neighbors=10))
        result = benchmark(deserialize_json, data)
        assert isinstance(result, dict)

    def test_orjson_deserialize_small(self, benchmark: Any) -> None:
        """Benchmark orjson deserialization of small message."""
        data = serialize_orjson(create_file_metadata(num_neighbors=10))
        result = benchmark(deserialize_orjson, data)
        assert isinstance(result, dict)

    def test_json_serialize_large(self, benchmark: Any) -> None:
        """Benchmark standard JSON serialization of large message."""
        data = create_file_metadata(num_neighbors=1000)
        result = benchmark(serialize_json, data)
        assert isinstance(result, bytes)

    def test_orjson_serialize_large(self, benchmark: Any) -> None:
        """Benchmark orjson serialization of large message."""
        data = create_file_metadata(num_neighbors=1000)
        result = benchmark(serialize_orjson, data)
        assert isinstance(result, bytes)

    def test_json_round_trip(self, benchmark: Any) -> None:
        """Benchmark standard JSON round trip (serialize + deserialize)."""
        data = create_file_metadata(num_neighbors=100)

        def round_trip() -> dict[str, Any]:
            serialized = serialize_json(data)
            return deserialize_json(serialized)

        result = benchmark(round_trip)
        assert result["file_path"] == data["file_path"]

    def test_orjson_round_trip(self, benchmark: Any) -> None:
        """Benchmark orjson round trip (serialize + deserialize)."""
        data = create_file_metadata(num_neighbors=100)

        def round_trip() -> dict[str, Any]:
            serialized = serialize_orjson(data)
            return deserialize_orjson(serialized)

        result = benchmark(round_trip)
        assert result["file_path"] == data["file_path"]
