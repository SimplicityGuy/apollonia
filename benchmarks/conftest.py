"""Configuration for benchmark tests."""


def pytest_addoption(parser):
    """Add custom command line options for benchmarks."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow benchmark tests",
    )


def pytest_configure(config):
    """Configure pytest for benchmarks."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m not slow')")


def pytest_benchmark_generate_json(config, benchmarks, include_data, machine_info, commit_info):
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
