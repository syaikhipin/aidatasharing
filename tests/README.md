# AI Share Platform - Test Suite

This directory contains the unified test suite for the AI Share Platform, providing comprehensive testing for both frontend and backend components.

## 🧪 Test Structure

### Core Test Files

- **`test_backend.py`** - Comprehensive backend API testing suite
- **`test_frontend.py`** - Frontend testing with Selenium WebDriver
- **`simple_test_runner.py`** - Simplified test runner (no browser automation required)
- **`run_all_tests.py`** - Advanced unified test runner with full automation
- **`run_tests.sh`** - Shell script wrapper for test execution

### Test Results

All test results are saved to the `test_results/` directory with timestamps:
- JSON results files for programmatic access
- Markdown reports for human-readable summaries

## 🚀 Running Tests

### Option 1: Simple Test Runner (Recommended)

```bash
# Run basic connectivity and API tests
python tests/simple_test_runner.py
```

**Features:**
- ✅ Frontend connectivity testing
- ✅ Backend API endpoint testing
- ✅ Registration flow testing
- ✅ Database connectivity testing
- ✅ No browser automation required
- ✅ Fast execution
- ✅ Detailed reports

### Option 2: Individual Test Suites

```bash
# Backend tests only
python tests/test_backend.py

# Frontend tests only (requires ChromeDriver)
python tests/test_frontend.py
```

### Option 3: Comprehensive Test Suite

```bash
# Full test suite with browser automation
python tests/run_all_tests.py
```

**Requirements:**
- ChromeDriver installed
- Both frontend and backend servers running

## 📋 Prerequisites

### Required Python Packages

```bash
pip install requests selenium pytest webdriver-manager
```

### Server Requirements

1. **Backend Server**: `http://localhost:8000`
   ```bash
   cd backend && python start.py
   ```

2. **Frontend Server**: `http://localhost:3000`
   ```bash
   cd frontend && npm run dev
   ```

### Optional: ChromeDriver

For full frontend testing with browser automation:
- Install ChromeDriver from https://chromedriver.chromium.org/
- Or use `webdriver-manager` (installed automatically)

## 📊 Test Coverage

### Backend Tests (19 tests)
- **Health Check** (3 tests)
  - Health endpoint
  - API documentation
  - OpenAPI schema
- **Authentication** (4 tests)
  - User registration
  - User login
  - Protected endpoints
  - Token validation
- **Organization Management** (4 tests)
  - Organization CRUD operations
  - Department management
  - Member management
- **Dataset Operations** (4 tests)
  - Dataset CRUD operations
  - File upload functionality
  - Permission management
- **Model Management** (4 tests)
  - Model creation and training
  - Model status monitoring
  - Prediction endpoints

### Frontend Tests (31 tests)
- **Landing Page** (4 tests)
  - Page loading
  - Navigation elements
  - Authentication links
- **Authentication Pages** (5 tests)
  - Login page functionality
  - Registration page functionality
  - Form validation
- **Protected Pages** (10 tests)
  - Dashboard access control
  - Route protection
  - Page accessibility
- **Responsive Design** (3 tests)
  - Desktop, tablet, mobile layouts
- **Navigation & Routing** (9 tests)
  - All major routes
  - 404 handling

### Simple Tests (17 tests)
- **Frontend Connectivity** (8 tests)
  - Server response
  - Page accessibility
  - Route handling
- **Backend API** (5 tests)
  - Health checks
  - Documentation endpoints
  - CORS configuration
- **Registration Flow** (2 tests)
  - Registration endpoint
  - Login functionality
- **Database Connectivity** (3 tests)
  - Data endpoints
  - Authentication requirements

## 📈 Test Results

### Latest Test Results
```
🎯 AI Share Platform Test Results:
   Frontend: ✅ Working (6/8 tests passed)
   Backend: ❌ Connection Issues (0/5 tests passed)
   Overall Success Rate: 35.3%
```

### Common Issues

1. **Backend Connection Timeout**
   - **Problem**: Backend server not responding on port 8000
   - **Solution**: Check backend logs, fix import errors, restart server

2. **Auth Page 404 Errors**
   - **Problem**: `/auth/login` and `/auth/register` return 404
   - **Solution**: Verify Next.js routing configuration

3. **ChromeDriver Issues**
   - **Problem**: Selenium tests fail to start browser
   - **Solution**: Install ChromeDriver or use simple test runner

## 🔧 Troubleshooting

### Backend Server Issues

1. **Check if server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check backend logs:**
   ```bash
   cd backend && tail -f backend.log
   ```

3. **Common fixes:**
   - Fix import errors in API modules
   - Resolve database connection issues
   - Check port conflicts

### Frontend Server Issues

1. **Check if server is running:**
   ```bash
   curl http://localhost:3000
   ```

2. **Restart frontend:**
   ```bash
   cd frontend && npm run dev
   ```

### Test Environment Setup

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   cd frontend && npm install
   ```

2. **Database initialization:**
   ```bash
   cd backend && python -c "from app.core.init_db import init_db; init_db()"
   ```

## 📝 Test Reports

Test reports are automatically generated in multiple formats:

- **JSON**: Machine-readable results with detailed test data
- **Markdown**: Human-readable reports with summaries and recommendations

### Sample Report Structure

```markdown
# AI Share Platform - Test Report
Generated: 2025-06-26 10:22:29

## Summary
- Total Tests: 17
- Passed: 6
- Failed: 11
- Success Rate: 35.3%

## Detailed Results
[Individual test results with pass/fail status and error details]

## Recommendations
[Specific recommendations based on test results]
```

## 🎯 Next Steps

1. **Fix Backend Issues**: Resolve server startup and connection problems
2. **Fix Auth Routes**: Ensure `/auth/login` and `/auth/register` are accessible
3. **Enhance Test Coverage**: Add more integration and end-to-end tests
4. **CI/CD Integration**: Add automated testing to deployment pipeline

## 📞 Support

For test-related issues:
1. Check server status and logs
2. Verify all dependencies are installed
3. Run simple test runner first for basic validation
4. Review detailed error messages in test reports 