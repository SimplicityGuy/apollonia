# Scripts Directory

This directory contains utility scripts for maintaining and updating the Apollonia project.

## Scripts

### update-project.sh

A comprehensive script for updating project dependencies and versions across the entire codebase.
This script provides a safe way to update both Python (backend) and Node.js (frontend) dependencies
with detailed tracking and rollback capabilities.

#### Features

- 🐍 **Python Version Management**: Updates Python version across all pyproject.toml files,
  Dockerfiles, and GitHub workflows
- 📦 **Python Package Updates**: Updates Python dependencies using UV package manager with detailed
  change tracking
- 🟢 **Node.js Version Management**: Updates Node.js version in Dockerfiles, workflows, and .nvmrc
  files
- 📦 **Node.js Package Updates**: Updates npm dependencies with major/minor version control
- 🐳 **UV Version Updates**: Automatically updates UV package manager to latest version
- 💾 **Backup System**: Creates timestamped backups before making changes
- 📝 **Change Tracking**: Provides detailed summary of all changes made
- 🧪 **Test Integration**: Optionally runs tests after updates
- 🎯 **Selective Updates**: Can update only frontend or backend dependencies

#### Usage

```bash
# Show help
./scripts/update-project.sh --help

# Dry run - see what would be updated
./scripts/update-project.sh --dry-run

# Update all dependencies (minor/patch versions only)
./scripts/update-project.sh

# Update including major version upgrades
./scripts/update-project.sh --major

# Update Python version
./scripts/update-project.sh --python 3.13

# Update Node.js version
./scripts/update-project.sh --node 20.10

# Update only frontend dependencies
./scripts/update-project.sh --frontend-only

# Update only backend dependencies
./scripts/update-project.sh --backend-only

# Skip tests after update
./scripts/update-project.sh --skip-tests

# Disable backup creation
./scripts/update-project.sh --no-backup
```

#### Options

- `--python VERSION`: Update Python version across the project
- `--node VERSION`: Update Node.js version across the project
- `--no-backup`: Skip creating backup files
- `--dry-run`: Show what would be updated without making changes
- `--major`: Include major version upgrades for packages
- `--skip-tests`: Skip running tests after updates
- `--frontend-only`: Only update frontend (Node.js) dependencies
- `--backend-only`: Only update backend (Python) dependencies
- `--help`: Show usage information

#### How It Works

1. **Pre-flight Checks**:

   - Verifies the script is run from project root
   - Checks for uncommitted changes (requires clean git state)
   - Ensures required tools are installed (uv, npm, jq, etc.)

1. **Backup Creation**:

   - Creates timestamped backup directory
   - Backs up all files before modification
   - Provides restore instructions if needed

1. **Update Process**:

   - Updates versions in configuration files using sed
   - Updates package dependencies using native tools (uv, npm)
   - Tracks all changes for summary report

1. **Post-Update**:

   - Optionally runs test suites
   - Generates comprehensive change summary
   - Provides git commands for committing changes
   - Lists manual verification steps

#### Requirements

- **Python Tools**: `uv` (UV package manager)
- **Node.js Tools**: `npm`, `npx`
- **System Tools**: `git`, `curl`, `jq`, `sed`
- **Clean Git State**: No uncommitted changes

#### Example Workflow

```bash
# 1. Check current status
git status  # Should be clean

# 2. Run dry-run to preview changes
./scripts/update-project.sh --dry-run

# 3. Run actual update
./scripts/update-project.sh

# 4. Review changes
git diff --stat
git diff uv.lock
git diff frontend/package-lock.json

# 5. Run manual verification
docker-compose build
docker-compose up -d
docker-compose ps

# 6. Commit changes
git add -A
git commit -m "chore: update dependencies"
```

#### Backup and Recovery

Backups are stored in `backups/project-updates-YYYYMMDD_HHMMSS/`.

To restore from backup:

```bash
# For Python dependencies
cp backups/project-updates-*/uv.lock.backup uv.lock
uv sync --all-extras

# For Node.js dependencies
cp backups/project-updates-*/frontend/package-lock.json.backup frontend/package-lock.json
cd frontend && npm ci
```

## Contributing

When adding new scripts:

1. Follow the existing naming convention (kebab-case)
1. Include comprehensive help/usage information
1. Add error handling and validation
1. Create backups before destructive operations
1. Provide clear output with emoji indicators
1. Update this README with documentation

## Best Practices

- Always run with `--dry-run` first
- Commit or stash changes before running update scripts
- Review all changes before committing
- Run tests and manual verification steps
- Keep scripts idempotent when possible
- Use meaningful exit codes
- Provide rollback instructions

## Future Scripts

Potential scripts to add:

- `check-security.sh`: Run security audits on dependencies
- `clean-docker.sh`: Clean up Docker artifacts and unused images
- `backup-data.sh`: Backup Neo4j and file data
- `deploy.sh`: Automated deployment script
- `benchmark.sh`: Performance benchmarking utilities
