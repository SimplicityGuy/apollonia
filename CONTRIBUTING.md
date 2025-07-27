# Contributing to Apollonia

Thank you for your interest in contributing to Apollonia! This guide will help you get started with
contributing to this media catalog system.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community and Support](#community-and-support)

## Code of Conduct

This project adheres to a code of conduct that ensures a welcoming environment for all contributors.
By participating, you are expected to uphold this standard.

### Our Standards

- **Be respectful**: Treat all community members with respect and kindness
- **Be inclusive**: Welcome newcomers and help them learn
- **Be collaborative**: Work together and share knowledge
- **Be professional**: Maintain a professional tone in all interactions
- **Be constructive**: Provide helpful feedback and suggestions

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.12+ installed
- Node.js 18+ for frontend development
- Docker and Docker Compose
- Git for version control
- [Just](https://just.systems/) task runner (recommended)

### Repository Structure

```
apollonia/
├── api/                    # FastAPI backend service
├── analyzer/              # ML analysis service
├── frontend/              # React frontend application
├── ingestor/              # File monitoring service
├── populator/             # Database population service
├── shared/                # Shared utilities
├── docs/                  # Documentation
├── tests/                 # Test suites
├── .github/workflows/     # CI/CD workflows
├── README.md              # Project overview
├── CLAUDE.md              # AI development guide
└── CONTRIBUTING.md        # This file
```

## Development Setup

### Quick Setup with Just

```bash
# Clone the repository
git clone https://github.com/SimplicityGuy/apollonia.git
cd apollonia

# Install Just (if not already installed)
cargo install just

# Set up development environment
just install

# Start all services
just up

# View available commands
just --list
```

### Manual Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Install frontend dependencies
cd frontend && npm ci && cd ..

# Start services
docker-compose up -d
```

## Contributing Process

### 1. Find or Create an Issue

- Browse [existing issues](https://github.com/SimplicityGuy/apollonia/issues)
- For new features, create an issue to discuss the proposal
- For bugs, check if the issue already exists

### 2. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/apollonia.git
cd apollonia

# Add upstream remote
git remote add upstream https://github.com/SimplicityGuy/apollonia.git
```

### 3. Create a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

## Development Workflow

### Daily Development

```bash
# Pull latest changes
git checkout main
git pull upstream main

# Create/switch to your feature branch
git checkout feature/your-feature-name

# Make your changes
# ...

# Run quality checks
just check

# Run tests
just test

# Commit your changes
git add .
git commit -m "feat: add your feature description"
```

### Branch Naming Conventions

- **Features**: `feature/feature-name`
- **Bug fixes**: `fix/bug-description`
- **Documentation**: `docs/topic-name`
- **Chores**: `chore/task-description`

## Code Standards

### Python Code Standards

- **Python Version**: Python 3.12+ (primary: 3.13)
- **Formatting**: Use `ruff format`
- **Linting**: Use `ruff check`
- **Type Checking**: Use `mypy`
- **Import Sorting**: Handled by `ruff`

```bash
# Run all Python quality checks
just lint
just format
just typecheck
```

### Frontend Code Standards

- **Framework**: React 18 with TypeScript
- **Formatting**: Prettier
- **Linting**: ESLint
- **Type Checking**: TypeScript compiler

```bash
# Run frontend quality checks
cd frontend
npm run lint
npm run format
npm run type-check
```

### Code Style Guidelines

1. **Follow existing patterns** in the codebase
1. **Use descriptive variable names**
1. **Write self-documenting code** with clear logic
1. **Add type hints** for all Python functions
1. **Use async/await** for I/O operations
1. **Follow SOLID principles** and clean architecture

### Emoji Logging Convention

All log messages should use emoji prefixes for visual clarity:

```python
logger.info("🚀 Starting service...")
logger.info("✅ Operation completed successfully")
logger.error("❌ Operation failed")
logger.warning("⚠️ Warning message")
```

See [Emoji Logging Convention](docs/development/logging-convention.md) for details.

## Testing Requirements

### Test Coverage Requirements

- **Minimum coverage**: 80% for new code
- **Unit tests**: Required for all new functions
- **Integration tests**: Required for service interactions
- **E2E tests**: Required for user-facing features

### Running Tests

```bash
# Run all tests
just test

# Run specific test types
just test-python        # Python unit tests
just test-frontend      # Frontend tests
just test-integration   # Integration tests
just test-e2e          # End-to-end tests

# Run with coverage
just test-coverage
```

### Writing Tests

1. **Unit Tests**: Test individual functions in isolation
1. **Integration Tests**: Test service interactions
1. **E2E Tests**: Test complete user workflows
1. **Mock external dependencies** appropriately
1. **Use descriptive test names** that explain the scenario

Example test structure:

```python
def test_should_process_audio_file_when_valid_format():
    # Given
    audio_file = create_test_audio_file()

    # When
    result = processor.process(audio_file)

    # Then
    assert result.is_successful
    assert result.metadata.format == "mp3"
```

## Documentation Guidelines

### Documentation Types

1. **Code Documentation**: Inline docstrings for functions/classes
1. **API Documentation**: OpenAPI/Swagger specs
1. **User Guides**: Step-by-step instructions
1. **Developer Guides**: Technical implementation details

### Writing Documentation

- **Use clear, concise language**
- **Include code examples** where helpful
- **Update documentation** when changing functionality
- **Follow naming conventions**:
  - Root files: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`
  - All others: lowercase with hyphens (e.g., `getting-started.md`)

### Documentation Standards

````markdown
# Title (H1 - one per document)

Brief description of the document's purpose.

## Section (H2)

Content with proper formatting:

- Use **bold** for emphasis
- Use `code` for technical terms
- Use ```language blocks for code examples
- Use > for important notes

### Subsection (H3)

More detailed content...
````

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
feat(api): add user authentication endpoint

fix(ingestor): handle corrupted media files gracefully

docs: update installation instructions

test(analyzer): add unit tests for audio processing

chore: update dependencies to latest versions
```

### Commit Message Body

- Explain **why** the change was made
- Reference issue numbers when applicable
- Keep lines under 72 characters

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: `just test`
1. **Run quality checks**: `just check`
1. **Update documentation** if needed
1. **Add/update tests** for new functionality
1. **Rebase on latest main**: `git rebase upstream/main`

### Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)

## Related Issues
Fixes #123
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
1. **At least one approval** from a maintainer
1. **All conversations resolved**
1. **Up-to-date with main branch**

### After Approval

1. **Squash and merge** for clean history
1. **Delete feature branch** after merge
1. **Update local repository**:

```bash
git checkout main
git pull upstream main
git branch -d feature/your-feature-name
```

## Community and Support

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

### Communication Guidelines

- **Be patient**: Maintainers are volunteers
- **Be specific**: Provide detailed information about issues
- **Be respectful**: Follow the code of conduct
- **Search first**: Check if your question has been asked

### Reporting Issues

When reporting bugs, include:

1. **Environment details**: OS, Python version, dependencies
1. **Steps to reproduce**: Clear, numbered steps
1. **Expected behavior**: What should happen
1. **Actual behavior**: What actually happens
1. **Error messages**: Full stack traces
1. **Screenshots**: If applicable

### Feature Requests

When requesting features:

1. **Describe the problem** you're trying to solve
1. **Propose a solution** with rationale
1. **Consider alternatives** and trade-offs
1. **Check existing issues** to avoid duplicates

## Development Tips

### Performance Considerations

- **Use async/await** for I/O operations
- **Implement caching** where appropriate
- **Monitor resource usage** during development
- **Profile code** for bottlenecks

### Security Best Practices

- **Never commit secrets** or credentials
- **Sanitize user inputs** properly
- **Use parameterized queries** for database operations
- **Follow security scanning results**

### Architecture Guidelines

- **Follow microservices patterns**
- **Use dependency injection** where appropriate
- **Implement proper error handling**
- **Design for scalability**

## Recognition

Contributors are recognized in:

- **GitHub contributors page**
- **Release notes** for significant contributions
- **Documentation credits** for major documentation work

Thank you for contributing to Apollonia! Your efforts help make this project better for everyone. 🎉
