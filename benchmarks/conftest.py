"""Configuration for benchmark tests."""

from typing import Any


def pytest_addoption(parser: Any) -> None:
    """Add custom command line options for benchmarks."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow benchmark tests",
    )


def pytest_configure(config: Any) -> None:
    """Configure pytest for benchmarks."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m not slow')")


def pytest_benchmark_generate_json(
    config: Any,
    benchmarks: list[Any],
    include_data: bool,
    machine_info: dict[str, Any],
    commit_info: dict[str, Any],
) -> dict[str, Any]:
    """Generate benchmark JSON report with custom metadata."""
    from datetime import datetime

    return {
        "benchmarks": benchmarks,
        "datetime": datetime.now().isoformat(),
        "machine_info": machine_info,
        "commit_info": commit_info,
        "version": "0.1.0",
        "benchmark_suite": "apollonia-performance",
    }
