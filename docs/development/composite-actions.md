# Composite Actions Documentation

This document describes the reusable composite actions used in Apollonia's GitHub workflows to
implement the DRY (Don't Repeat Yourself) principle and improve maintainability.

## Overview

Composite actions are reusable workflow components that combine multiple steps into a single action.
They help:

- Eliminate code duplication across workflows
- Standardize environment setup
- Simplify workflow maintenance
- Ensure consistent configuration

## Available Actions

### setup-python-env

**Location**: `.github/actions/setup-python-env/action.yml`

**Purpose**: Standardized Python environment setup with uv package manager and intelligent caching.

**Inputs**:

- `python-version` (default: '3.12'): Python version to install
- `install-just` (default: 'true'): Whether to install the just command runner
- `install-dependencies` (default: 'true'): Whether to install Python dependencies
- `dependency-groups` (default: '--frozen --all-extras'): Dependency groups to install
- `cache-key-prefix` (default: 'python'): Cache key prefix for dependency caching

**Outputs**:

- `python-version`: The installed Python version
- `cache-hit`: Whether the cache was hit

**Usage Example**:

```yaml
- name: Setup Python environment
  uses: ./.github/actions/setup-python-env
  with:
    python-version: '3.12'
    install-just: true
    cache-key-prefix: python-test-unit
```

**Features**:

- Installs uv with built-in caching
- Sets up specified Python version
- Caches Python dependencies (uv cache, pip cache, .venv)
- Optionally installs just task runner
- Flexible dependency installation

### setup-frontend-env

**Location**: `.github/actions/setup-frontend-env/action.yml`

**Purpose**: Node.js environment setup with npm caching and dependency installation.

**Inputs**:

- `node-version` (default: '22'): Node.js version to install
- `working-directory` (default: 'frontend'): Working directory for frontend
- `install-dependencies` (default: 'true'): Whether to install dependencies
- `install-just` (default: 'false'): Whether to install just command runner
- `cache-key-prefix` (default: 'frontend'): Cache key prefix for dependency caching

**Outputs**:

- `cache-hit`: Whether the cache was hit

**Usage Example**:

```yaml
- name: Setup frontend environment
  uses: ./.github/actions/setup-frontend-env
  with:
    node-version: '22'
    working-directory: frontend
    install-just: true
```

**Features**:

- Sets up Node.js with npm cache
- Caches node_modules and npm cache
- Conditional dependency installation (skipped if cache hit)
- Supports custom working directories
- Optionally installs just task runner

## Implementation Details

### Caching Strategy

Both actions implement multi-layer caching:

1. **Dependency Manager Cache**: uv/npm built-in caching
1. **Package Cache**: Virtual environments and node_modules
1. **Lock File Based Keys**: Cache invalidation on dependency changes

### Cache Key Construction

**Python Cache Key**:

```
{prefix}-{os}-py{version}-{hash(pyproject.toml, uv.lock)}
```

**Frontend Cache Key**:

```
{prefix}-{os}-node{version}-{hash(package-lock.json)}
```

### Conditional Logic

- Dependencies are only installed if not cached
- Just is only installed when explicitly requested
- Working directory is configurable for monorepo support

## Benefits

### Performance Improvements

- **Reduced Setup Time**: ~70% faster with cache hits
- **Parallel Execution**: Actions can run concurrently
- **Smart Caching**: Only rebuilds when dependencies change

### Maintenance Benefits

- **Single Source of Truth**: Update setup in one place
- **Consistent Configuration**: Same setup across all workflows
- **Version Management**: Centralized tool version control
- **Easy Updates**: Change versions without editing multiple files

### Developer Experience

- **Clear Interfaces**: Well-documented inputs and outputs
- **Flexible Usage**: Configurable for different scenarios
- **Error Prevention**: Validated inputs and sensible defaults
- **Debugging Support**: Clear output messages

## Usage Guidelines

### When to Use

- **Always** for Python/Node.js setup in workflows
- **Multiple Jobs**: When setup is needed in multiple jobs
- **Consistency**: To ensure identical environments

### Best Practices

1. **Cache Key Prefixes**: Use descriptive prefixes for different contexts
1. **Dependency Groups**: Only install what's needed
1. **Version Pinning**: Specify exact versions for reproducibility
1. **Cache Validation**: Monitor cache hit rates

### Common Patterns

**Testing Workflows**:

```yaml
- uses: ./.github/actions/setup-python-env
  with:
    cache-key-prefix: python-test-${{ matrix.test-group }}
```

**Build Workflows**:

```yaml
- uses: ./.github/actions/setup-frontend-env
  with:
    install-just: true  # Need build commands
```

**Quick Checks**:

```yaml
- uses: ./.github/actions/setup-python-env
  with:
    install-dependencies: false  # Just need Python
```

## Troubleshooting

### Cache Misses

**Symptoms**: Slow workflow runs, dependencies reinstalled

**Solutions**:

- Check if lock files changed
- Verify cache key construction
- Review cache size limits

### Version Conflicts

**Symptoms**: Different Python/Node versions than expected

**Solutions**:

- Explicitly specify versions
- Check for matrix strategy conflicts
- Verify action version compatibility

### Permission Issues

**Symptoms**: Cache write failures

**Solutions**:

- Ensure workflow has write permissions
- Check GitHub Actions cache limits
- Verify repository settings

## Future Enhancements

### Planned Improvements

1. **Multi-Version Support**: Test against multiple versions easily
1. **Platform Support**: Windows and macOS optimizations
1. **Tool Integration**: More development tools (poetry, pnpm)
1. **Performance Metrics**: Built-in timing and reporting

### Contribution Guidelines

To modify composite actions:

1. Test changes locally first
1. Update documentation
1. Version changes appropriately
1. Test in a PR before merging
1. Update all workflows using the action

## Examples

### Complete Python Setup

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python with all features
        uses: ./.github/actions/setup-python-env
        with:
          python-version: '3.12'
          install-just: true
          cache-key-prefix: full-test

      - name: Run tests
        run: just test
```

### Minimal Frontend Setup

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js only
        uses: ./.github/actions/setup-frontend-env
        with:
          install-dependencies: false

      - name: Install specific package
        run: npm install eslint
```

### Matrix Strategy

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']

steps:
  - uses: ./.github/actions/setup-python-env
    with:
      python-version: ${{ matrix.python-version }}
      cache-key-prefix: test-py${{ matrix.python-version }}
```
