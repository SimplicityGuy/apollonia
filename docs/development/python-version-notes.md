# Python Version Configuration

## Primary Target: Python 3.13

The Apollonia project is configured to target Python 3.13 as its primary version:

- All `pyproject.toml` files specify `requires-python = ">=3.13"`
- Docker images use `python:3.13-alpine`
- Ruff is configured with `target-version = "py313"`
- MyPy is set to `python_version = "3.13"`

## Compatibility Testing: Python 3.12

While the project targets Python 3.13, the CI/CD pipeline includes Python 3.12 in the test matrix to
ensure backward compatibility:

```yaml
python-version: ['3.12', '3.13']  # Test on 3.12 for compatibility, 3.13 as primary
```

The CI workflow handles this by:

1. Testing both Python 3.12 and 3.13 in the matrix
1. Using relaxed dependency resolution for Python 3.12 (`uv sync --all-extras`)
1. Using frozen dependencies for Python 3.13 (`uv sync --frozen --all-extras`)

## Rationale

- **Python 3.13** provides the latest performance improvements and language features
- **Python 3.12** compatibility ensures broader deployment options and smoother migration paths
- The project uses no Python 3.13-specific syntax, maintaining compatibility

## Future Considerations

When Python 3.14 is released:

1. Add 3.14 to the CI test matrix
1. Consider dropping 3.12 support after a transition period
1. Update to target 3.14 when ecosystem support is mature
