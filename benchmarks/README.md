# Apollonia Performance Benchmarks

This directory contains performance benchmarks for critical operations in the Apollonia system.

## Running Benchmarks

### Run all benchmarks

```bash
just test-benchmarks
```

### Run specific benchmark tests

```bash
uv run pytest benchmarks/test_hash_performance.py -v
```

### Run with detailed output

```bash
uv run pytest benchmarks/ --benchmark-verbose
```

### Run including slow tests

```bash
uv run pytest benchmarks/ --run-slow
```

### Generate comparison report

```bash
uv run pytest benchmarks/ --benchmark-compare=.benchmarks/0001_baseline.json
```

## Benchmark Categories

### Hash Performance (`test_hash_performance.py`)

- Compares SHA256 vs xxHash128 performance
- Tests with different file sizes (1MB, 10MB, 100MB)
- Helps optimize file hashing strategy

### Message Processing (`test_message_processing.py`)

- Compares standard JSON vs orjson serialization
- Tests serialization/deserialization performance
- Benchmarks round-trip operations

### Neo4j Operations (`test_neo4j_operations.py`)

- Tests single node insertion
- Benchmarks node creation with relationships
- Evaluates batch insertion performance

## Benchmark Results

Benchmark results are stored in:

- `benchmark-results.json` - Latest results in pytest-benchmark format
- `.benchmarks/` - Historical benchmark data for comparisons

## Adding New Benchmarks

1. Create a new test file in the `benchmarks/` directory
1. Use the `benchmark` fixture provided by pytest-benchmark
1. Follow the naming convention: `test_<component>_performance.py`
1. Document what the benchmark measures and why it's important

Example:

```python
def test_my_operation(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result == expected_value
```

## Performance Targets

- File hashing: \<100ms for 10MB files
- Message serialization: \<1ms for typical messages
- Neo4j single insert: \<10ms average
- Neo4j batch insert: \<1ms per node for batches of 100+
