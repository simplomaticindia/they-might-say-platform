# Testing Guide - They Might Say

This guide provides comprehensive instructions for testing the They Might Say platform locally and in production.

## 🧪 Quick Test Commands

### Run All Tests
```bash
# Comprehensive test suite (recommended)
python run_all_tests.py

# With specific options
python run_all_tests.py --backend-only
python run_all_tests.py --frontend-only
python run_all_tests.py --skip-e2e
python run_all_tests.py --verbose
```

### Individual Test Suites
```bash
# Backend API tests
cd backend && pytest tests/ -v

# Frontend unit tests
cd frontend && npm test

# Frontend E2E tests
cd frontend && npm run test:e2e

# Type checking
cd frontend && npm run type-check

# Linting
cd frontend && npm run lint
```

## 🚀 Local Development Testing

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd they-might-say

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Update .env files with your API keys
```

### 2. Docker Testing (Recommended)
```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
docker-compose logs -f

# Run tests against running services
python run_all_tests.py

# Stop services
docker-compose down
```

### 3. Manual Testing Setup

#### Backend Testing
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Testing
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# In another terminal, run tests
npm test
```

## 🔍 Test Coverage

### Backend Test Coverage
- **Authentication**: JWT token generation, validation, refresh
- **API Endpoints**: All CRUD operations for users, sources, episodes
- **Database Models**: Pydantic schema validation
- **File Processing**: Upload, text extraction, chunking
- **Vector Search**: Embedding generation, similarity search
- **WebSocket**: Real-time communication testing

### Frontend Test Coverage
- **Components**: UI component rendering and interactions
- **API Client**: HTTP requests, error handling, WebSocket connections
- **Authentication**: Login/logout flows, token management
- **File Upload**: Drag-and-drop, progress tracking, validation
- **Studio Mode**: Chat interface, real-time updates, citation display

### E2E Test Coverage
- **User Authentication**: Complete login/logout flow
- **Source Management**: File upload and processing workflow
- **Studio Mode**: End-to-end conversation testing
- **Episode Management**: Create, edit, and manage episodes
- **Cross-browser**: Chrome, Firefox, Safari testing

## 📊 Test Results Interpretation

### Backend Test Results
```bash
# Expected output
================================ test session starts ================================
collected 25 items

tests/test_auth.py::test_create_access_token PASSED                          [ 4%]
tests/test_auth.py::test_verify_token PASSED                                [ 8%]
tests/test_sources.py::test_upload_file PASSED                              [12%]
tests/test_sources.py::test_process_document PASSED                         [16%]
tests/test_studio.py::test_create_conversation PASSED                       [20%]
tests/test_studio.py::test_websocket_connection PASSED                      [24%]
...

========================== 25 passed, 0 failed in 15.23s ==========================
```

### Frontend Test Results
```bash
# Expected output
PASS  __tests__/components/ui/button.test.tsx
PASS  __tests__/components/studio/chat-message.test.tsx
PASS  __tests__/lib/api-client.test.ts

Test Suites: 3 passed, 3 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        3.456 s
```

### E2E Test Results
```bash
# Expected output
Running 8 tests using 1 worker

  ✓ [chromium] › studio-mode.spec.ts:3:1 › Studio Mode › should load chat interface (2.1s)
  ✓ [chromium] › studio-mode.spec.ts:15:1 › Studio Mode › should send and receive messages (3.4s)
  ✓ [chromium] › studio-mode.spec.ts:28:1 › Studio Mode › should display citations (2.8s)
  ...

  8 passed (12.3s)
```

## 🐛 Troubleshooting Common Issues

### Backend Issues

#### Database Connection Errors
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql postgresql://postgres:password@localhost:5432/theymightsay

# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

#### OpenAI API Errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping
```

### Frontend Issues

#### Node.js Version Issues
```bash
# Check Node.js version (requires 18+)
node --version

# Install correct version
nvm install 18
nvm use 18
```

#### Dependency Installation Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Build Issues
```bash
# Check TypeScript compilation
npm run type-check

# Check for linting errors
npm run lint

# Clear Next.js cache
rm -rf .next
npm run build
```

### E2E Testing Issues

#### Browser Installation
```bash
# Install Playwright browsers
npx playwright install

# Install system dependencies
npx playwright install-deps
```

#### Test Timeout Issues
```bash
# Increase timeout in playwright.config.ts
timeout: 60000  // 60 seconds

# Run with debug mode
npx playwright test --debug
```

## 🔧 Test Configuration

### Backend Test Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Frontend Test Configuration
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/e2e/'],
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}
```

### E2E Test Configuration
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
})
```

## 📈 Performance Testing

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load tests
artillery run load-test.yml

# Monitor performance
docker stats
```

### Memory Testing
```bash
# Backend memory usage
python -m memory_profiler backend/main.py

# Frontend bundle analysis
cd frontend
npm run analyze
```

## 🚀 CI/CD Testing

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run comprehensive tests
        run: python run_all_tests.py
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📝 Test Reporting

### Coverage Reports
```bash
# Backend coverage
cd backend
pytest --cov=. --cov-report=html

# Frontend coverage
cd frontend
npm test -- --coverage --watchAll=false

# View reports
open backend/htmlcov/index.html
open frontend/coverage/lcov-report/index.html
```

### Test Documentation
```bash
# Generate test documentation
cd backend
pytest --collect-only --quiet

cd frontend
npm test -- --listTests
```

---

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. **Check the logs**: `docker-compose logs -f`
2. **Verify environment**: Ensure all `.env` variables are set
3. **Database state**: Check if migrations are up to date
4. **API connectivity**: Test backend endpoints directly
5. **Browser console**: Check for JavaScript errors

For additional support, please refer to the main README.md or create an issue in the repository.