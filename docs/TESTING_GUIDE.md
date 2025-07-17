# AI Share Platform - Testing Guide

## 🧪 Comprehensive Testing Documentation

This guide provides step-by-step instructions for testing the AI Share Platform to ensure all components are working correctly.

## 📋 Pre-Testing Setup

### 1. Fresh Installation
```bash
# Ensure you have a clean installation
python setup_fresh_install.py

# Verify the installation completed successfully
ls -la storage/aishare_platform.db  # Should exist
```

### 2. Environment Verification
```bash
# Check environment configuration
cat .env | grep -E "(DATABASE_URL|GOOGLE_API_KEY|MINDSDB_URL)"

# Verify backend configuration
cat backend/.env | grep DATABASE_URL

# Verify frontend configuration
cat frontend/.env.local | grep NEXT_PUBLIC_API_URL
```

### 3. Dependencies Check
```bash
# Backend dependencies
cd backend && pip list | grep -E "(fastapi|sqlalchemy|pydantic)"

# Frontend dependencies
cd ../frontend && npm list --depth=0 | grep -E "(next|react|typescript)"
```

## 🔧 Automated Testing

### 1. Run All Tests
```bash
# Navigate to tests directory
cd tests

# Run comprehensive test suite
python run_all_tests.py

# Expected output: All tests should pass
# ✅ Backend API Tests: PASSED
# ✅ Frontend Tests: PASSED  
# ✅ Document Processing Tests: PASSED
# ✅ Integration Tests: PASSED
```

### 2. Individual Test Categories

#### Backend API Tests
```bash
cd tests
python test_backend.py

# Tests covered:
# - Authentication endpoints
# - Dataset management APIs
# - Document processing APIs
# - Data connector APIs
# - User management
# - Organization management
```

#### Document Processing Tests
```bash
cd tests
python test_document_processing.py

# Tests covered:
# - PDF text extraction
# - DOCX processing
# - TXT file handling
# - Document metadata extraction
# - AI chat model creation
```

#### Frontend Component Tests
```bash
cd tests
python test_frontend.py

# Tests covered:
# - Component rendering
# - API integration
# - File upload functionality
# - Navigation and routing
```

#### Integration Tests
```bash
cd tests
python test_complete_system_fullflow_01_20250710_152829.py

# Tests covered:
# - End-to-end user workflows
# - Data sharing functionality
# - AI chat integration
# - Multi-user scenarios
```

## 🚀 Manual Testing Procedures

### 1. System Startup Test

#### Start the Development Environment
```bash
# From project root
./start-dev.sh

# Expected output:
# 🚀 Starting AI Share Platform Development Environment...
# 📦 Activating conda environment: aishare-platform
# 🔧 Starting backend server...
# 🎨 Starting frontend server...
# ✅ Development environment started!
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

#### Verify Services are Running
```bash
# Check backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Check frontend accessibility
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

### 2. Authentication Testing

#### Admin Login Test
1. **Navigate to**: http://localhost:3000/login
2. **Enter credentials**:
   - Email: `admin@aishare.com`
   - Password: `admin123`
3. **Expected result**: Successful login, redirect to dashboard
4. **Verify**: Admin panel access available

#### API Authentication Test
```bash
# Get authentication token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@aishare.com", "password": "admin123"}'

# Expected response:
# {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Dataset Management Testing

#### File Upload Test
1. **Navigate to**: http://localhost:3000/datasets
2. **Click**: "Upload Dataset" button
3. **Upload a CSV file** (use `tests/data/sample.csv` if available)
4. **Expected result**: 
   - Upload progress indicator
   - Success message
   - Dataset appears in list

#### Document Upload Test
1. **Navigate to**: http://localhost:3000/datasets
2. **Click**: "Upload Document" button
3. **Upload a PDF/DOCX file**
4. **Expected result**:
   - Document processing indicator
   - Text extraction preview
   - AI chat model creation

#### Data Connector Test
1. **Navigate to**: http://localhost:3000/datasets/connect
2. **Select**: MySQL connector
3. **Enter test connection details**:
   - Host: `localhost`
   - Port: `3306`
   - Database: `test`
   - Username: `test`
   - Password: `test`
4. **Expected result**: Connection validation (may fail if no MySQL, but UI should work)

### 4. AI Integration Testing

#### Document Chat Test
1. **Upload a document** (PDF or DOCX)
2. **Navigate to dataset detail page**
3. **Use AI chat feature**:
   - Enter: "What is this document about?"
4. **Expected result**: AI response based on document content

#### Dataset Analysis Test
1. **Upload a CSV dataset**
2. **Navigate to dataset detail page**
3. **Use AI chat feature**:
   - Enter: "Analyze this dataset"
4. **Expected result**: AI-generated insights about the data

### 5. Data Sharing Testing

#### Create Share Link Test
1. **Navigate to dataset detail page**
2. **Click**: "Share" button
3. **Configure sharing options**:
   - Set expiration: 24 hours
   - Enable AI chat: Yes
4. **Expected result**: Shareable link generated

#### Access Shared Dataset Test
1. **Copy the share link** from previous test
2. **Open in incognito/private browser**
3. **Access the shared dataset**
4. **Expected result**: 
   - Dataset accessible without login
   - AI chat available (if enabled)
   - Download available (if enabled)

### 6. Admin Panel Testing

#### User Management Test
1. **Navigate to**: http://localhost:3000/admin
2. **Go to**: Users section
3. **Create a new user**:
   - Email: `test@example.com`
   - Name: `Test User`
   - Role: `Member`
4. **Expected result**: User created successfully

#### Organization Management Test
1. **Navigate to**: Admin → Organizations
2. **View organization details**
3. **Update organization settings**
4. **Expected result**: Settings saved successfully

### 7. Analytics Testing

#### Usage Analytics Test
1. **Navigate to**: http://localhost:3000/analytics
2. **View dashboard metrics**:
   - Dataset count
   - User activity
   - Storage usage
3. **Expected result**: Analytics data displayed correctly

## 🔍 API Testing with Curl

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@aishare.com", "password": "admin123"}'

# Store token for subsequent requests
TOKEN="your-token-here"
```

### Dataset Operations
```bash
# List datasets
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/datasets

# Get dataset details
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/datasets/1

# Upload file (multipart)
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@tests/data/sample.csv" \
  -F "name=Test Dataset" \
  http://localhost:8000/api/datasets/upload
```

### Document Processing
```bash
# Upload document
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@tests/data/sample.pdf" \
  -F "dataset_name=Test Document" \
  http://localhost:8000/api/data-connectors/document

# Get supported document types
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/data-connectors/supported-types
```

### Data Connectors
```bash
# Create MySQL connector
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test MySQL",
    "connector_type": "mysql",
    "connection_config": {
      "host": "localhost",
      "port": 3306,
      "database": "test"
    },
    "credentials": {
      "user": "test",
      "password": "test"
    }
  }' \
  http://localhost:8000/api/data-connectors
```

## 🐛 Troubleshooting Common Issues

### Backend Issues

#### Database Connection Error
```bash
# Check database file exists
ls -la storage/aishare_platform.db

# Check database permissions
chmod 664 storage/aishare_platform.db

# Recreate database if needed
python migrations/fresh_install_migration.py
```

#### Import Errors
```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Port Already in Use
```bash
# Kill existing processes
pkill -f "uvicorn"
pkill -f "python.*start.py"

# Check port usage
lsof -i :8000
```

### Frontend Issues

#### Node.js Dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Build Errors
```bash
cd frontend
npm run build
# Check for TypeScript errors
```

#### API Connection Issues
```bash
# Check environment variables
cat frontend/.env.local

# Verify backend is running
curl http://localhost:8000/health
```

### Document Processing Issues

#### Missing Libraries
```bash
# Install document processing libraries
pip install PyMuPDF python-docx docx2txt striprtf odfpy

# Test document processing
cd tests
python test_simple_document.py
```

#### File Upload Issues
```bash
# Check upload directory permissions
ls -la storage/uploads/
chmod 755 storage/uploads/

# Check file size limits
grep MAX_FILE_SIZE .env
```

## ✅ Test Checklist

### Pre-Testing
- [ ] Fresh installation completed
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Database created and migrated

### Automated Tests
- [ ] Backend API tests pass
- [ ] Document processing tests pass
- [ ] Frontend component tests pass
- [ ] Integration tests pass

### Manual Tests
- [ ] System starts successfully
- [ ] Admin login works
- [ ] File upload works
- [ ] Document processing works
- [ ] Data connectors work
- [ ] AI chat works
- [ ] Data sharing works
- [ ] Admin panel works
- [ ] Analytics display correctly

### API Tests
- [ ] Authentication endpoints work
- [ ] Dataset CRUD operations work
- [ ] Document processing API works
- [ ] Data connector API works
- [ ] Sharing API works

### Performance Tests
- [ ] File upload performance acceptable
- [ ] Document processing completes
- [ ] AI responses generated
- [ ] Database queries perform well

## 📊 Expected Test Results

### Successful Test Output
```
🧪 AI Share Platform Test Suite
================================

✅ Backend API Tests: PASSED (15/15)
✅ Document Processing: PASSED (8/8)
✅ Frontend Tests: PASSED (12/12)
✅ Integration Tests: PASSED (6/6)
✅ Database Tests: PASSED (5/5)

🎉 All tests passed successfully!
📊 Total: 46/46 tests passed
⏱️  Total time: 2m 34s
```

### Test Coverage Areas
- **Authentication**: Login, logout, token validation
- **Dataset Management**: CRUD operations, file uploads
- **Document Processing**: Text extraction, metadata analysis
- **Data Connectors**: Database connections, validation
- **AI Integration**: Chat functionality, model creation
- **Data Sharing**: Link creation, access control
- **User Management**: User CRUD, role management
- **Organization Management**: Multi-tenant operations
- **File Handling**: Upload, download, storage
- **API Security**: Authorization, input validation

## 🚀 Ready for Production

Once all tests pass, the system is ready for:
- **Development**: Local development environment
- **Staging**: Pre-production testing
- **Production**: Live deployment

---

*This testing guide ensures comprehensive validation of all AI Share Platform features and functionality.*