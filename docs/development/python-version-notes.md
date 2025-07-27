# Python Version Configuration

## Target: Python 3.12

The Apollonia project is configured to target Python 3.12:

- All `pyproject.toml` files specify `requires-python = "~=3.12.0"`
- Docker images use `python:3.12-alpine` or `python:3.12-slim`
- Ruff is configured with `target-version = "py312"`
- MyPy is set to `python_version = "3.12"`

## TensorFlow Compatibility

The primary reason for targeting Python 3.12 is TensorFlow compatibility. TensorFlow and related ML
libraries (including essentia-tensorflow) do not yet support Python 3.13.

## Benefits of Python 3.12

- **Stable Ecosystem**: All required dependencies are available and well-tested
- **Performance**: Python 3.12 includes significant performance improvements over earlier versions
- **Type Improvements**: Enhanced type hinting capabilities for better static analysis
- **Error Messages**: Improved error messages for easier debugging

## Future Considerations

When TensorFlow and essentia-tensorflow add support for Python 3.13:

1. Update all `pyproject.toml` files to support Python 3.13
1. Add Python 3.13 to the CI test matrix
1. Update Docker base images as appropriate
