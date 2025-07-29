# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Apollonia project.

## Workflow Overview

### Main CI Pipeline (`ci.yml`)

The main CI workflow that orchestrates all checks in parallel:

- Runs on all pushes and pull requests to main
- Executes quality checks, tests, and Docker builds concurrently
- Provides a unified status check

### Individual Workflows

#### `test.yml` - Comprehensive Testing

- **Python Tests**: Run in parallel across multiple test groups
  - Unit tests
  - Integration tests (without Docker)
  - Analyzer tests
  - API tests
  - E2E unit tests
- **Frontend Tests**: JavaScript/TypeScript tests with coverage
- **Integration Tests**: Tests requiring external services (RabbitMQ, Neo4j, etc.)
- **E2E Tests**: Full end-to-end tests with Docker Compose
- **Coverage**: All tests generate coverage reports uploaded to Codecov

#### `quality.yml` - Code Quality Checks

- Backend linting (Ruff)
- Frontend linting (ESLint)
- Type checking (mypy for Python, TypeScript)
- Security scanning (Bandit, npm audit)
- Pre-commit hooks validation

#### `docker.yml` - Container Build & Deploy

- Builds all service containers
- Security scanning with Trivy
- Multi-platform builds (linux/amd64)
- Optional push to GitHub Container Registry

#### `dependencies.yml` - Dependency Management

- Weekly automated dependency updates
- Security vulnerability scanning
- Automated PR creation for updates

#### `build.yml` - Manual Build Verification

- On-demand workflow for build verification
- Tests all build configurations

## Coverage Configuration

### Codecov Integration

- All test jobs upload coverage to Codecov
- Coverage flags for different test types:
  - `unit`: Python unit tests
  - `integration-unit`: Integration unit tests
  - `integration`: Full integration tests
  - `frontend`: Frontend JavaScript tests
  - `backend`: Combined backend coverage

### Coverage Targets

- Overall project: 80%
- Frontend: 70%
- Backend: 80%
- New code (patch): 85%

## Parallelization Strategy

All workflows are designed to run in parallel for maximum efficiency:

1. **Test Parallelization**:

   - Python tests split by test type and directory
   - Each test group runs independently
   - Coverage files combined at the end

1. **Service Parallelization**:

   - Docker builds run in parallel
   - Quality checks run concurrently
   - Independent workflows can execute simultaneously

1. **Resource Optimization**:

   - Smart caching for dependencies
   - Docker layer caching
   - Test result caching
   - Conditional execution based on file changes

## Running Workflows Locally

```bash
# Run specific workflow manually
gh workflow run test.yml

# Run CI pipeline
gh workflow run ci.yml

# Build and push Docker images
gh workflow run docker.yml -f push_images=true

# Update dependencies
gh workflow run dependencies.yml -f update_type=minor
```

## Workflow Secrets

Required secrets for full functionality:

- `CODECOV_TOKEN`: For coverage uploads
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Best Practices

1. **Always run tests in parallel** when possible
1. **Use workflow_call** to enable workflow reusability
1. **Enable coverage** for all test runs
1. **Use matrix builds** to test multiple configurations
1. **Cache aggressively** to improve performance
1. **Set appropriate timeouts** to prevent hanging jobs
1. **Use concurrency groups** to cancel outdated runs
