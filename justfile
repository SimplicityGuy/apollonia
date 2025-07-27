# Apollonia Project Justfile
# https://just.systems/

# Default recipe to display help
default:
  @just --list

# Set shell for Windows compatibility
set windows-shell := ["powershell.exe", "-c"]

# Project variables
export COMPOSE_PROJECT_NAME := "apollonia"
export DOCKER_BUILDKIT := "1"

# Python variables
python_version := "3.12"
venv := ".venv"

# ========== Development Setup ==========
[group('setup')]
install:
  #!/usr/bin/env bash
  echo "🚀 Installing Apollonia development environment..."
  if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  echo "📦 Installing Python dependencies..."
  uv sync --all-extras
  echo "🪝 Installing pre-commit hooks..."
  uv run pre-commit install
  echo "✅ Development environment ready!"

[group('setup')]
install-hooks:
  uv run pre-commit install
  uv run pre-commit install --hook-type commit-msg

[group('setup')]
update-deps:
  uv lock --upgrade
  uv sync --all-extras

# ========== Build Tasks ==========
[group('build')]
build: build-services build-frontend
  echo "✅ All components built successfully!"

[group('build')]
build-services:
  #!/usr/bin/env bash
  echo "🔨 Building microservices..."
  for service in ingestor analyzer populator api; do
    echo "  📦 Building $service..."
    docker build -t apollonia-$service ./$service
  done

[group('build')]
build-frontend:
  echo "🎨 Building frontend..."
  cd frontend && npm ci && npm run build

[group('build')]
build-docker:
  echo "🐳 Building all Docker images..."
  docker-compose build --parallel

[group('build')]
build-docker-no-cache:
  echo "🐳 Building all Docker images (no cache)..."
  docker-compose build --parallel --no-cache

# ========== Test Tasks ==========
[group('test')]
test: test-python test-frontend
  echo "✅ All tests passed!"

[group('test')]
test-python:
  echo "🧪 Running Python tests..."
  uv run pytest -v

[group('test')]
test-python-watch:
  echo "👁️ Running Python tests in watch mode..."
  uv run pytest-watch

[group('test')]
test-coverage:
  echo "📊 Running tests with coverage..."
  uv run pytest --cov=. --cov-report=html --cov-report=term

[group('test')]
test-integration:
  echo "🔗 Running integration tests..."
  uv run pytest tests/integration -v

[group('test')]
test-e2e:
  echo "🌐 Running end-to-end tests..."
  docker-compose up -d
  sleep 10  # Wait for services to start
  uv run pytest tests/e2e -v
  docker-compose down

[group('test')]
test-frontend:
  echo "🎨 Running frontend tests..."
  cd frontend && npm test

[group('test')]
test-frontend-watch:
  echo "👁️ Running frontend tests in watch mode..."
  cd frontend && npm run test:watch

# ========== Quality Checks ==========
[group('quality')]
check: lint typecheck format-check
  echo "✅ All quality checks passed!"

[group('quality')]
lint:
  echo "🔍 Running linters..."
  uv run ruff check .
  cd frontend && npm run lint

[group('quality')]
lint-fix:
  echo "🔧 Fixing linting issues..."
  uv run ruff check --fix .
  cd frontend && npm run lint -- --fix

[group('quality')]
format:
  echo "💅 Formatting code..."
  uv run ruff format .
  cd frontend && npm run format

[group('quality')]
format-check:
  echo "💅 Checking code formatting..."
  uv run ruff format --check .
  cd frontend && npm run format -- --check

[group('quality')]
typecheck:
  echo "🔍 Running type checkers..."
  uv run mypy .
  cd frontend && npm run type-check

[group('quality')]
pre-commit:
  echo "🪝 Running pre-commit hooks..."
  uv run pre-commit run --all-files

# ========== Docker & Services ==========
[group('docker')]
up:
  echo "🚀 Starting all services..."
  docker-compose up -d
  @just logs -f

[group('docker')]
down:
  echo "🛑 Stopping all services..."
  docker-compose down

[group('docker')]
restart service="":
  #!/usr/bin/env bash
  if [ -z "{{service}}" ]; then
    echo "🔄 Restarting all services..."
    docker-compose restart
  else
    echo "🔄 Restarting {{service}}..."
    docker-compose restart {{service}}
  fi

[group('docker')]
logs service="" *args="":
  #!/usr/bin/env bash
  if [ -z "{{service}}" ]; then
    docker-compose logs {{args}}
  else
    docker-compose logs {{service}} {{args}}
  fi

[group('docker')]
ps:
  docker-compose ps

[group('docker')]
exec service *cmd:
  docker-compose exec {{service}} {{cmd}}

# ========== Database Tasks ==========
[group('db')]
db-migrate:
  echo "🗄️ Running database migrations..."
  cd api && uv run alembic upgrade head

[group('db')]
db-rollback steps="1":
  echo "⏮️ Rolling back {{steps}} migration(s)..."
  cd api && uv run alembic downgrade -{{steps}}

[group('db')]
db-reset:
  echo "🔄 Resetting database..."
  docker-compose down -v postgres
  docker-compose up -d postgres
  sleep 5
  @just db-migrate

[group('db')]
db-shell:
  echo "🐘 Connecting to PostgreSQL..."
  docker-compose exec postgres psql -U apollonia -d apollonia

[group('db')]
neo4j-shell:
  echo "🔷 Connecting to Neo4j..."
  docker-compose exec neo4j cypher-shell -u neo4j -p apollonia

# ========== Development Tasks ==========
[group('dev')]
dev:
  #!/usr/bin/env bash
  echo "🚀 Starting development environment..."
  # Start backend services
  docker-compose up -d rabbitmq postgres redis neo4j
  sleep 5
  # Run migrations
  just db-migrate
  # Start services in separate terminals if possible
  if command -v tmux &> /dev/null; then
    tmux new-session -d -s apollonia-dev
    tmux send-keys -t apollonia-dev:0 "just run-api" C-m
    tmux split-window -t apollonia-dev:0 -v
    tmux send-keys -t apollonia-dev:0.1 "just run-frontend" C-m
    tmux split-window -t apollonia-dev:0 -h
    tmux send-keys -t apollonia-dev:0.2 "just run-analyzer" C-m
    tmux attach -t apollonia-dev
  else
    echo "💡 Tip: Install tmux for better development experience"
    echo "Starting services in background..."
    just run-api &
    just run-frontend &
    just run-analyzer &
    wait
  fi

[group('dev')]
run-api:
  echo "🌐 Starting API service..."
  cd api && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

[group('dev')]
run-frontend:
  echo "🎨 Starting frontend dev server..."
  cd frontend && npm run dev

[group('dev')]
run-ingestor:
  echo "👁️ Starting media ingestor..."
  uv run python -m ingestor

[group('dev')]
run-analyzer:
  echo "🧠 Starting ML analyzer..."
  uv run python -m analyzer

[group('dev')]
run-populator:
  echo "💾 Starting database populator..."
  uv run python -m populator

# ========== Cleanup Tasks ==========
[group('clean')]
clean: clean-python clean-frontend clean-docker
  echo "✨ Cleanup complete!"

[group('clean')]
clean-python:
  echo "🧹 Cleaning Python artifacts..."
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
  find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
  find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
  find . -type f -name "*.pyc" -delete 2>/dev/null || true
  find . -type f -name "*.pyo" -delete 2>/dev/null || true
  find . -type f -name ".coverage" -delete 2>/dev/null || true
  rm -rf htmlcov/ 2>/dev/null || true

[group('clean')]
clean-frontend:
  echo "🧹 Cleaning frontend artifacts..."
  rm -rf frontend/node_modules frontend/dist frontend/.vite 2>/dev/null || true

[group('clean')]
clean-docker:
  echo "🐳 Cleaning Docker artifacts..."
  docker-compose down -v --remove-orphans
  docker system prune -f

[group('clean')]
clean-all: clean
  echo "💥 Deep cleaning..."
  rm -rf .venv/ 2>/dev/null || true
  docker system prune -af --volumes

# ========== Utility Tasks ==========
[group('util')]
tree:
  tree -I '__pycache__|*.pyc|node_modules|.git|.venv|dist|build|*.egg-info' -a

[group('util')]
todo:
  echo "📝 TODOs in codebase:"
  rg "TODO|FIXME|HACK|XXX" --type py --type ts --type tsx

[group('util')]
outdated:
  echo "📦 Checking for outdated dependencies..."
  echo "Python packages:"
  uv pip list --outdated
  echo -e "\nFrontend packages:"
  cd frontend && npm outdated

[group('util')]
security:
  echo "🔒 Running security checks..."
  uv run pip-audit
  cd frontend && npm audit

[group('util')]
env-template:
  echo "📄 Generating .env.template..."
  echo "# Apollonia Environment Variables" > .env.template
  echo "" >> .env.template
  rg "os\.getenv|process\.env" -o -N | \
    sed 's/os.getenv[("'\'']*//g' | \
    sed 's/process.env.//g' | \
    sed 's/[)"'\'',].*//g' | \
    sort | uniq | \
    awk '{print $0"="}' >> .env.template

# ========== Documentation ==========
[group('docs')]
docs-serve:
  echo "📚 Serving documentation..."
  cd docs && python -m http.server 8080

[group('docs')]
docs-build:
  echo "📚 Building documentation..."
  uv run mkdocs build

# ========== Release Tasks ==========
[group('release')]
version-bump part="patch":
  #!/usr/bin/env bash
  echo "📦 Bumping version ({{part}})..."
  # Bump version in pyproject.toml files
  for f in pyproject.toml */pyproject.toml; do
    if [ -f "$f" ]; then
      current=$(grep "^version = " "$f" | cut -d'"' -f2)
      echo "Current version in $f: $current"
    fi
  done
  echo "⚠️  Manual version bump required - update pyproject.toml files"

[group('release')]
changelog:
  echo "📝 Generating changelog..."
  echo "⚠️  Manual changelog generation required"

[group('release')]
release: check test
  echo "🚀 Preparing release..."
  echo "1. Bump version"
  echo "2. Update CHANGELOG.md"
  echo "3. Commit changes"
  echo "4. Tag release"
  echo "5. Push to repository"
  echo "⚠️  Manual release process required"

# ========== Help & Info ==========
help:
  @just --list

info:
  @echo "Apollonia Media Catalog System"
  @echo "=============================="
  @echo "Python: {{python_version}}"
  @echo "Virtual Environment: {{venv}}"
  @echo ""
  @echo "Quick Start:"
  @echo "  just install    # Set up development environment"
  @echo "  just up         # Start all services"
  @echo "  just dev        # Start development mode"
  @echo "  just test       # Run all tests"
  @echo "  just check      # Run quality checks"
  @echo ""
  @echo "For more commands: just --list"
