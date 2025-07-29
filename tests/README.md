# Apollonia Test Suite Documentation

This document provides comprehensive documentation for the Apollonia test suite, including unit
tests, integration tests, and end-to-end tests.

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Fixtures and Utilities](#fixtures-and-utilities)
- [Mocking Strategies](#mocking-strategies)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_ingestor.py    # Ingestor service unit tests
│   └── test_populator.py   # Populator service unit tests
├── ingestor/               # Ingestor-specific tests
│   └── test_prospector.py  # File prospecting unit tests
├── integration/            # Integration tests
│   ├── test_ingestor_integration.py
│   ├── test_populator_integration.py
│   └── test_end_to_end.py
├── e2e/                    # End-to-end tests
│   ├── conftest.py         # E2E test configuration
│   ├── test_frontend_e2e.py
│   └── test_docker_e2e.py
├── conftest.py             # Shared pytest configuration
└── README.md               # This file

frontend/
├── src/
│   ├── pages/*.test.tsx    # Page component tests
│   ├── components/ui/*.test.tsx  # UI component tests
│   └── utils/*.test.ts     # Utility function tests
└── vitest.config.ts        # Vitest configuration
```

## Running Tests

### Backend Python Tests

```bash
# Run all Python tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test categories
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only
uv run pytest -m integration       # Tests marked as integration
uv run pytest -m "not integration" # Exclude integration tests

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_ingestor.py

# Run specific test
uv run pytest tests/unit/test_ingestor.py::TestIngestor::test_ingestor_initialization
```

### Frontend React Tests

```bash
cd frontend/

# Run all frontend tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test src/pages/HomePage.test.tsx

# Run tests matching pattern
npm test -- --grep "navigation"
```

### End-to-End Tests

```bash
# Install Playwright browsers (first time only)
cd tests/e2e && npm install && npx playwright install

# Run frontend E2E tests
pytest tests/e2e/test_frontend_e2e.py

# Run Docker E2E tests (requires Docker)
pytest tests/e2e/test_docker_e2e.py -m docker

# Run with headed browser (see what's happening)
pytest tests/e2e/test_frontend_e2e.py --headed

# Run specific browser
pytest tests/e2e/test_frontend_e2e.py --browser chromium
pytest tests/e2e/test_frontend_e2e.py --browser firefox
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **Ingestor Tests** (`test_ingestor.py`):

  - Initialization and configuration
  - AMQP connection handling
  - File event processing
  - Error handling and recovery
  - Signal handling

- **Populator Tests** (`test_populator.py`):

  - Neo4j connection management
  - Message processing from AMQP
  - Graph node creation and updates
  - Error handling and retries

- **Prospector Tests** (`test_prospector.py`):

  - File metadata extraction
  - Hash computation (SHA256, xxh128)
  - Neighbor file discovery
  - Edge case handling (permissions, symlinks)

### Integration Tests

Integration tests verify that components work together correctly:

- **Service Integration**:

  - AMQP message flow between services
  - Neo4j graph construction
  - End-to-end file processing pipeline
  - Service resilience and recovery

- **Platform Compatibility**:

  - Tests are marked to skip on incompatible platforms when needed
  - Docker-based tests for full system integration

### End-to-End Tests

E2E tests verify the complete user experience:

- **Frontend E2E**:

  - User authentication flow
  - File upload and management
  - Navigation and routing
  - Responsive design
  - Error handling

- **Docker E2E**:

  - Complete system deployment
  - Service health checks
  - Data persistence
  - Performance monitoring

## Fixtures and Utilities

### Common Fixtures

```python
# Backend fixtures (conftest.py)
@pytest.fixture
def mock_amqp_connection():
    """Mock AMQP connection for testing."""
    connection = Mock(spec=BlockingConnection)
    # ... configuration
    return connection

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for file tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

# Frontend fixtures (test utils)
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

const renderWithQueryClient = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      {component}
    </QueryClientProvider>
  )
}
```

### Test Data Factories

```python
# Create test file data
def create_test_file_data(filename="test.txt", size=1024):
    return {
        "file_path": f"/test/{filename}",
        "sha256_hash": "abc123",
        "xxh128_hash": "def456",
        "size": size,
        "modified_time": "2024-01-01T00:00:00",
        "event_type": "IN_CREATE",
        "neighbors": []
    }

# Create test user data
const createTestUser = (overrides = {}) => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  ...overrides
})
```

## Mocking Strategies

### Python Mocking

```python
# Mock external services
with patch("ingestor.ingestor.BlockingConnection") as mock_conn:
    mock_conn.return_value = mock_amqp_connection
    # ... test code

# Mock async functions
mock_driver = AsyncMock(spec=AsyncDriver)
mock_driver.session.return_value.__aenter__.return_value = session

# Mock file system operations
with patch("pathlib.Path.open", mock_open(read_data="test content")):
    # ... test code
```

### React/TypeScript Mocking

```typescript
// Mock API calls
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: mockData }),
    post: vi.fn().mockResolvedValue({ data: { success: true } })
  }
}))

// Mock hooks
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    user: mockUser,
    login: vi.fn(),
    logout: vi.fn()
  })
}))

// Mock router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn()
  }
})
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# Run Python tests
- name: Run Python tests
  run: |
    uv run pytest --cov=. --cov-report=xml

# Run Frontend tests
- name: Run Frontend tests
  working-directory: ./frontend
  run: |
    npm ci
    npm run test:coverage

# Run E2E tests
- name: Run E2E tests
  run: |
    docker-compose up -d
    pytest tests/e2e/ -m docker
    docker-compose down
```

### Coverage Requirements

- **Python Backend**: Minimum 80% coverage
- **React Frontend**: Minimum 75% coverage
- **Critical Paths**: 100% coverage for authentication, file processing

## Best Practices

### Test Writing Guidelines

1. **Descriptive Names**: Use clear, descriptive test names that explain what is being tested

   ```python
   def test_ingestor_handles_missing_file_gracefully():
       # NOT: def test_error():
   ```

1. **Arrange-Act-Assert**: Structure tests clearly

   ```python
   def test_file_processing():
       # Arrange
       test_file = create_test_file()

       # Act
       result = process_file(test_file)

       # Assert
       assert result.status == "success"
   ```

1. **Test One Thing**: Each test should verify a single behavior

1. **Use Fixtures**: Reuse common setup through fixtures

1. **Mock External Dependencies**: Don't rely on external services in unit tests

### Platform-Specific Considerations

1. **Linux-Only Features**: Mark tests that require Linux

   ```python
   @pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific test")
   ```

1. **Docker Tests**: Mark tests that require Docker

   ```python
   @pytest.mark.docker
   @pytest.mark.slow
   ```

1. **Browser Tests**: Configure for multiple browsers

   ```python
   @pytest.mark.parametrize("browser_name", ["chromium", "firefox"])
   ```

### Performance Testing

1. **Mark Slow Tests**: Use pytest markers

   ```python
   @pytest.mark.slow
   def test_large_file_processing():
       # Test that might take > 1 second
   ```

1. **Set Timeouts**: Prevent hanging tests

   ```python
   @pytest.mark.timeout(30)
   def test_with_timeout():
       # Test must complete within 30 seconds
   ```

### Data Cleanup

1. **Use Fixtures for Cleanup**:

   ```python
   @pytest.fixture
   async def neo4j_cleanup():
       yield
       # Cleanup runs after test
       async with driver.session() as session:
           await session.run("MATCH (n:TestNode) DELETE n")
   ```

1. **Temporary Files**: Always use temp directories

   ```python
   with tempfile.TemporaryDirectory() as tmpdir:
       # Files are automatically cleaned up
   ```

## Debugging Tests

### Python Tests

```bash
# Run with debugging output
pytest -vv -s

# Drop into debugger on failure
pytest --pdb

# Run specific test with logging
pytest tests/unit/test_ingestor.py::test_name -v --log-cli-level=DEBUG
```

### Frontend Tests

```bash
# Run with debugging
npm test -- --reporter=verbose

# Run single test file
npm test src/pages/HomePage.test.tsx

# Debug in VS Code
# Add breakpoints and use "Debug Test" lens in VS Code
```

### E2E Tests

```bash
# Run with headed browser to see what's happening
pytest tests/e2e/test_frontend_e2e.py --headed

# Slow down execution
pytest tests/e2e/test_frontend_e2e.py --slowmo=1000

# Save trace for debugging
pytest tests/e2e/test_frontend_e2e.py --tracing=on
```

## Common Issues and Solutions

### Issue: Integration tests fail due to missing services

**Solution**: Check that RabbitMQ and Neo4j are running:

```bash
docker-compose up -d rabbitmq neo4j
```

### Issue: E2E tests timeout

**Solution**: Increase timeout in conftest.py or specific tests:

```python
page.wait_for_selector("element", timeout=30000)  # 30 seconds
```

### Issue: Flaky tests

**Solution**: Use proper waiting strategies:

```python
# Bad: time.sleep(2)
# Good:
await page.wait_for_selector(".loaded")
await expect(element).to_be_visible()
```

## Contributing Tests

When adding new features:

1. Write tests first (TDD approach)
1. Ensure tests are independent and can run in any order
1. Add appropriate markers for test categories
1. Update this documentation if adding new patterns
1. Ensure CI passes before merging

## Test Maintenance

1. **Regular Review**: Review and update tests quarterly
1. **Remove Obsolete Tests**: Delete tests for removed features
1. **Update Mocks**: Keep mocks in sync with actual implementations
1. **Performance Monitoring**: Track test suite execution time
1. **Coverage Monitoring**: Maintain and improve coverage metrics
