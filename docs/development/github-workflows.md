# GitHub Workflows Documentation

Apollonia uses GitHub Actions for comprehensive CI/CD automation. The workflows are designed with a
DevOps-first approach, emphasizing security, quality, and reliability.

## Workflow Overview

### Main Pipeline (`build.yml`)

The orchestrating workflow that coordinates all other workflows:

- **Triggers**: Push to main, PRs, weekly schedule, manual dispatch
- **Dependencies**: quality → tests → docker + security
- **Features**:
  - Overall status reporting
  - Performance benchmarking
  - Dependency review for PRs
  - Security scanning with CodeQL

### Quality Checks (`quality.yml`)

Fast feedback loop for code quality:

- **Purpose**: Quick validation of code standards
- **Scope**: Python linting, formatting, type checking, frontend quality
- **Tools**: Ruff, mypy, ESLint, Prettier, bandit
- **Runtime**: ~3-5 minutes
- **Parallel execution** across Python 3.12 and 3.13

### Testing Suite (`test.yml`)

Comprehensive testing pipeline:

- **Python Tests**: Unit tests with coverage across multiple Python versions
- **Frontend Tests**: React component and integration tests
- **Integration Tests**: Real services (RabbitMQ, PostgreSQL, Neo4j, Redis)
- **E2E Tests**: Full system testing with Docker Compose
- **Coverage**: Codecov integration for both Python and frontend

### Docker Build (`docker.yml`)

Container build and deployment pipeline:

- **Service Discovery**: Auto-detects services with Dockerfiles
- **Multi-platform**: Builds for linux/amd64 and linux/arm64
- **Security**: Trivy vulnerability scanning
- **Registry**: GitHub Container Registry (ghcr.io)
- **Integration Testing**: Multi-service deployment validation

### Deployment (`deploy.yml`)

Production deployment workflows:

- **Environments**: Staging and production
- **Triggers**: Releases (prod) or manual dispatch
- **Features**:
  - Health checks and monitoring updates
  - Rollback capabilities
  - Slack/Discord notifications
  - Environment protection rules

### Dependencies (`dependencies.yml`)

Automated dependency management:

- **Schedule**: Weekly on Monday at 2 AM UTC
- **Scope**: Python (uv) and Node.js packages
- **Levels**: Patch, minor, major, or all updates
- **Automation**: Creates PRs with test results
- **Security**: Vulnerability scanning

## Workflow Features

### 🔒 Security-First Design

**Multi-layer Security Scanning**:

- **Trivy**: Container vulnerability scanning
- **CodeQL**: Static code analysis
- **Bandit**: Python security linting
- **pip-audit**: Python dependency scanning
- **npm audit**: Node.js dependency scanning

**SARIF Integration**: Security findings uploaded to GitHub Security tab

**Secrets Management**: Minimal secret usage with GitHub token authentication

### 📊 Quality Gates

**8-Step Validation Cycle**:

1. Syntax validation
1. Type checking
1. Linting and formatting
1. Security scanning
1. Unit testing
1. Integration testing
1. E2E testing
1. Deployment validation

### ⚡ Performance Optimizations

**Intelligent Caching**:

- uv cache for Python dependencies
- npm cache for Node.js dependencies
- Docker layer caching with GitHub Actions cache

**Parallel Execution**:

- Matrix builds across Python versions
- Concurrent workflow execution
- Service-specific Docker builds

**Resource Management**:

- Concurrency controls to prevent resource conflicts
- Automatic cancellation of outdated runs
- Optimized artifact storage

### 🎯 Developer Experience

**Visual Feedback**:

- Emoji-enhanced step names for better readability
- Comprehensive status summaries
- Artifact uploads for debugging

**Fast Feedback**:

- Quality checks complete in ~3-5 minutes
- Parallel test execution
- Early failure detection

## Environment Variables

### Required Secrets

```bash
# Docker registry (automatic)
GITHUB_TOKEN=<automatic>

# Code coverage
CODECOV_TOKEN=<optional>

# Notifications
DISCORD_WEBHOOK=<optional>
SLACK_WEBHOOK=<optional>

# Container registry (automatic)
GHCR_TOKEN=<automatic>
```

### Workflow Environment Variables

```yaml
# Container registry settings
REGISTRY: ghcr.io
IMAGE_NAME: ${{ github.actor }}/apollonia

# Test database settings
AMQP_CONNECTION_STRING: amqp://test:test@localhost:5672/
NEO4J_URI: bolt://localhost:7687
NEO4J_USER: neo4j
NEO4J_PASSWORD: testpassword
```

## Triggering Workflows

### Automatic Triggers

**On every push to main**:

- Quality checks
- Full test suite
- Docker builds (with push)
- Security scanning

**On every pull request**:

- Quality checks
- Full test suite
- Docker builds (no push)
- Dependency review

**Weekly schedule**:

- Dependency updates (Monday 2 AM UTC)
- Full pipeline run (Saturday 1 AM UTC)

### Manual Triggers

**Workflow Dispatch Options**:

```bash
# Deploy to specific environment
gh workflow run deploy.yml -f environment=staging -f version=v1.2.3

# Force Docker image push
gh workflow run docker.yml -f push_images=true

# Dependency update level
gh workflow run dependencies.yml -f update_type=minor
```

## Monitoring and Observability

### Status Badges

Add to your README:

```markdown
![CI/CD](https://github.com/username/apollonia/actions/workflows/build.yml/badge.svg)
![Quality](https://github.com/username/apollonia/actions/workflows/quality.yml/badge.svg)
![Tests](https://github.com/username/apollonia/actions/workflows/test.yml/badge.svg)
```

### Notifications

**Discord Integration**:

- Build status notifications
- Deployment status updates
- Security alert summaries

**Slack Integration**:

- Deployment notifications
- Rollback alerts

### Metrics and Reporting

**Test Results**:

- JUnit XML reports
- Coverage reports (Codecov)
- Performance benchmarks

**Security Reports**:

- SARIF uploads to GitHub Security
- Vulnerability artifact uploads
- Dependency audit reports

## Development Workflow Integration

### Local Development

```bash
# Run quality checks locally (matches CI)
just check

# Run tests locally
just test

# Build Docker images locally
just build-docker

# Full CI simulation
just check && just test && just build-docker
```

### Pre-commit Integration

The workflows integrate with pre-commit hooks:

```bash
# Install hooks (done by `just install`)
uv run pre-commit install

# Run hooks manually
just pre-commit
```

## Troubleshooting

### Common Issues

**Workflow Validation Errors**:

- Check YAML syntax with `yamllint`
- Validate workflows with GitHub CLI: `gh workflow validate`

**Docker Build Failures**:

- Check Dockerfile syntax
- Verify base image availability
- Review build context size

**Test Failures**:

- Check service dependencies in GitHub services
- Verify environment variable configuration
- Review test isolation

### Debugging Workflows

**Artifact Downloads**:

```bash
# Download workflow artifacts
gh run download <run-id>
```

**Workflow Logs**:

```bash
# View workflow run logs
gh run view <run-id> --log
```

**Re-run Failed Jobs**:

```bash
# Re-run failed jobs only
gh run rerun <run-id> --failed
```

## Best Practices

### Workflow Design

1. **Fast Feedback**: Quality checks run first and fast
1. **Parallel Execution**: Independent jobs run concurrently
1. **Fail Fast**: Early detection and reporting of issues
1. **Resource Efficiency**: Intelligent caching and artifact management

### Security

1. **Minimal Secrets**: Use GitHub tokens when possible
1. **Scoped Permissions**: Least privilege access
1. **Vulnerability Scanning**: Multiple security tools
1. **Audit Trail**: Comprehensive logging and reporting

### Maintenance

1. **Version Pinning**: Use specific action versions
1. **Regular Updates**: Keep actions and dependencies current
1. **Documentation**: Keep workflow docs up to date
1. **Testing**: Validate workflow changes in PRs

## Future Enhancements

### Planned Improvements

- **Progressive Deployment**: Blue/green deployments
- **Environment Promotion**: Automated staging → production
- **Performance Regression**: Automated performance testing
- **Security Baseline**: Security posture tracking

### Monitoring Enhancements

- **Workflow Analytics**: Success rates and performance metrics
- **Cost Optimization**: Resource usage tracking
- **Alert Tuning**: Reduce noise, improve signal
- **Dashboard Integration**: Central DevOps dashboard
