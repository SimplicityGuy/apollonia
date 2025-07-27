# Justfile Command Reference

The Apollonia project uses [Just](https://just.systems/) as a command runner to simplify development
workflows. All common tasks are organized into logical groups.

## Installation

```bash
# Install Just
cargo install just

# Or on macOS
brew install just

# Or on Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
```

## Command Groups

### Setup Commands

```bash
just install          # Complete development environment setup
just install-hooks    # Install git pre-commit hooks
just update-deps      # Update and sync all dependencies
```

### Build Commands

```bash
just build            # Build all components (services + frontend)
just build-services   # Build only microservices
just build-frontend   # Build only frontend
just build-docker     # Build all Docker images
just build-docker-no-cache  # Build Docker images without cache
```

### Test Commands

```bash
just test             # Run all tests
just test-python      # Run Python tests
just test-python-watch # Run Python tests in watch mode
just test-coverage    # Run tests with coverage report
just test-integration # Run integration tests
just test-e2e         # Run end-to-end tests
just test-frontend    # Run frontend tests
just test-frontend-watch # Run frontend tests in watch mode
```

### Quality Commands

```bash
just check            # Run all quality checks
just lint             # Run linters
just lint-fix         # Fix linting issues
just format           # Format all code
just format-check     # Check code formatting
just typecheck        # Run type checkers
just pre-commit       # Run pre-commit hooks on all files
```

### Docker Commands

```bash
just up               # Start all services
just down             # Stop all services
just restart [service] # Restart all or specific service
just logs [service] [-f] # View logs
just ps               # List running containers
just exec <service> <cmd> # Execute command in container
```

### Database Commands

```bash
just db-migrate       # Run database migrations
just db-rollback [n]  # Rollback n migrations (default: 1)
just db-reset         # Reset database completely
just db-shell         # Connect to PostgreSQL
just neo4j-shell      # Connect to Neo4j
```

### Development Commands

```bash
just dev              # Start full dev environment (tmux recommended)
just run-api          # Start API service
just run-frontend     # Start frontend dev server
just run-ingestor     # Start media ingestor
just run-analyzer     # Start ML analyzer
just run-populator    # Start database populator
```

### Cleanup Commands

```bash
just clean            # Clean all artifacts
just clean-python     # Clean Python artifacts
just clean-frontend   # Clean frontend artifacts
just clean-docker     # Clean Docker artifacts
just clean-all        # Deep clean everything
```

### Utility Commands

```bash
just tree             # Show project structure
just todo             # Find TODOs in codebase
just outdated         # Check for outdated dependencies
just security         # Run security checks
just env-template     # Generate .env.template file
```

### Documentation Commands

```bash
just docs-serve       # Serve documentation locally
just docs-build       # Build documentation
```

### Release Commands

```bash
just version-bump [part] # Bump version (patch/minor/major)
just changelog        # Generate changelog
just release          # Prepare release
```

## Common Workflows

### Initial Setup

```bash
# Clone repository
git clone https://github.com/apollonia/apollonia.git
cd apollonia

# Install development environment
just install

# Start services
just up
```

### Development Workflow

```bash
# Start development environment
just dev

# Or start services individually
just up
just run-api          # In one terminal
just run-frontend     # In another terminal

# Run tests while developing
just test-python-watch
```

### Before Committing

```bash
# Run all checks
just check

# Fix issues
just lint-fix
just format

# Run tests
just test
```

### Working with Docker

```bash
# Start services
just up

# View logs
just logs -f

# Restart a service
just restart api

# Execute commands
just exec api bash
just exec postgres psql -U apollonia
```

### Database Management

```bash
# Run migrations
just db-migrate

# Reset database
just db-reset

# Connect to database
just db-shell
```

## Tips

1. **Use `just --list`** to see all available commands with descriptions
1. **Tab completion** is available - see
   [Just documentation](https://just.systems/man/en/shell-completion.html)
1. **Grouped commands** can be filtered: `just --list --list-heading 'Test Commands'`
1. **Dry run** commands with `just --dry-run <command>`
1. **Set variables** with `just <command> variable=value`

## Customization

You can create a `.justfile` in your home directory for personal aliases:

```just
# ~/.justfile
alias t := test
alias c := check
alias u := up
```

## Environment Variables

The Justfile respects these environment variables:

- `COMPOSE_PROJECT_NAME`: Docker Compose project name (default: "apollonia")
- `DOCKER_BUILDKIT`: Enable Docker BuildKit (default: "1")

## Troubleshooting

### Command not found

```bash
# Ensure Just is in your PATH
which just

# Or use full path
/usr/local/bin/just --list
```

### Permission denied

```bash
# Some commands may need sudo
sudo just clean-docker
```

### Services won't start

```bash
# Check Docker status
docker ps

# Reset everything
just clean-all
just install
just up
```
