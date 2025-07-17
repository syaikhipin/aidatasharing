# Manual Testing Checklist

## 🧪 Pre-Testing Setup

### ✅ System Verification
- [ ] Run offline tests: `cd tests && python test_offline_verification.py`
- [ ] All offline tests pass (37/37)
- [ ] Database file exists: `ls -la storage/aishare_platform.db`
- [ ] Environment configured: Check `.env` file has required variables

### ✅ Start Development Environment
```bash
# From project root
./start-dev.sh

# Expected output:
# 🚀 Starting AI Share Platform Development Environment...
# 🔧 Starting backend server...
# 🎨 Starting frontend server...
# ✅ Development environment started!
```

### ✅ Verify Services
- [ ] Backend health: `curl http://localhost:8000/health` → `{"status": "healthy"}`
- [ ] Frontend accessible: Open http://localhost:3000 → Page loads
- [ ] API docs accessible: Open http://localhost:8000/docs → Swagger UI loads

---

## 🔐 Authentication Testing

### ✅ Admin Login
1. **Navigate to**: http://localhost:3000/login
2. **Enter credentials**:
   - Email: `admin@aishare.com`
   - Password: `admin123`
3. **Expected**: ✅ Successful login, redirect to dashboard
4. **Verify**: Admin panel accessible in navigation

### ✅ API Authentication
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@aishare.com", "password": "admin123"}'

# Expected: {"access_token": "eyJ...", "token_type": "bearer"}
```

---

## 📊 Dataset Management Testing

### ✅ Dataset List Page
1. **Navigate to**: http://localhost:3000/datasets
2. **Expected**: 
   - [ ] Page loads without errors
   - [ ] "Upload Dataset" button visible
   - [ ] "Upload Document" button visible
   - [ ] "Connect Data Source" button visible

### ✅ CSV File Upload
1. **Click**: "Upload Dataset" button
2. **Create test CSV file**:
   ```csv
   name,age,city
   John,25,New York
   Jane,30,Los Angeles
   Bob,35,Chicago
   ```
3. **Upload file** and fill form:
   - Name: "Test CSV Dataset"
   - Description: "Test CSV upload"
4. **Expected**: 
   - [ ] Upload progress indicator
   - [ ] Success message
   - [ ] Dataset appears in list

### ✅ Document Upload
1. **Click**: "Upload Document" button
2. **Create test document** (save as test.txt):
   ```
   This is a test document for the AI Share Platform.
   It contains sample text for document processing.
   The platform should extract this text automatically.
   ```
3. **Upload document** and fill form:
   - Dataset Name: "Test Document"
   - Description: "Test document upload"
   - Sharing Level: "Private"
4. **Expected**:
   - [ ] Upload progress indicator
   - [ ] Document processing message
   - [ ] Dataset created with extracted text

---

## 🔗 Data Connector Testing

### ✅ Data Source Connection Page
1. **Navigate to**: http://localhost:3000/datasets/connect
2. **Expected**:
   - [ ] Page loads with connector tabs
   - [ ] MySQL, PostgreSQL, S3 tabs visible
   - [ ] Form fields for each connector type

### ✅ MySQL Connector Test
1. **Select**: MySQL tab
2. **Fill form** (test values):
   - Name: "Test MySQL Connection"
   - Host: `localhost`
   - Port: `3306`
   - Database: `test`
   - Username: `test`
   - Password: `test`
3. **Click**: "Connect Data Source"
4. **Expected**: 
   - [ ] Validation attempt (may fail if no MySQL, but UI should work)
   - [ ] Appropriate error/success message

---

## 🤖 AI Integration Testing

### ✅ Dataset AI Chat
1. **Navigate to**: Dataset detail page (any uploaded dataset)
2. **Find**: AI chat section
3. **Enter question**: "What insights can you provide about this dataset?"
4. **Expected**:
   - [ ] Chat interface responds
   - [ ] AI generates response (may be generic if no API key)
   - [ ] No JavaScript errors

### ✅ Document Chat
1. **Navigate to**: Document dataset detail page
2. **Use AI chat**: "What is this document about?"
3. **Expected**:
   - [ ] Document-specific chat interface
   - [ ] AI response based on document content
   - [ ] Text preview visible

---

## 📤 Data Sharing Testing

### ✅ Create Share Link
1. **Navigate to**: Any dataset detail page
2. **Click**: "Share" button
3. **Configure sharing**:
   - Expiration: 24 hours
   - Password: (optional)
   - Enable AI chat: Yes
4. **Expected**:
   - [ ] Share link generated
   - [ ] Link is copyable
   - [ ] Share settings saved

### ✅ Access Shared Dataset
1. **Copy share link** from previous test
2. **Open in incognito/private browser**
3. **Access shared dataset**
4. **Expected**:
   - [ ] Dataset accessible without login
   - [ ] Data preview visible
   - [ ] AI chat available (if enabled)
   - [ ] Download works (if enabled)

---

## 👥 Admin Panel Testing

### ✅ User Management
1. **Navigate to**: http://localhost:3000/admin
2. **Go to**: Users section
3. **Create new user**:
   - Email: `test@example.com`
   - Name: `Test User`
   - Role: `Member`
4. **Expected**:
   - [ ] User creation form works
   - [ ] User appears in list
   - [ ] User can be edited/deleted

### ✅ Organization Management
1. **Navigate to**: Admin → Organizations
2. **View**: Organization details
3. **Update**: Organization settings
4. **Expected**:
   - [ ] Organization info displayed
   - [ ] Settings can be modified
   - [ ] Changes are saved

---

## 📈 Analytics Testing

### ✅ Analytics Dashboard
1. **Navigate to**: http://localhost:3000/analytics
2. **Expected**:
   - [ ] Dashboard loads without errors
   - [ ] Metrics displayed (may be zero for new installation)
   - [ ] Charts/graphs render correctly
   - [ ] No console errors

---

## 🔧 API Testing (Optional)

### ✅ Core API Endpoints
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@aishare.com", "password": "admin123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Test datasets endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/datasets

# Test user profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/users/me

# Test supported connectors
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/data-connectors/supported-types
```

---

## 🚨 Error Testing

### ✅ Error Handling
1. **Test invalid login**: Wrong email/password
2. **Test file upload limits**: Upload very large file
3. **Test invalid file types**: Upload unsupported file
4. **Test network errors**: Disconnect internet during upload
5. **Expected**: 
   - [ ] Appropriate error messages
   - [ ] No application crashes
   - [ ] User can recover from errors

---

## 📱 Responsive Design Testing

### ✅ Mobile/Tablet Testing
1. **Open browser dev tools**
2. **Switch to mobile view**
3. **Test key pages**:
   - [ ] Login page
   - [ ] Dashboard
   - [ ] Dataset list
   - [ ] Upload forms
4. **Expected**:
   - [ ] Pages are responsive
   - [ ] All functionality accessible
   - [ ] No horizontal scrolling

---

## 🎯 Performance Testing

### ✅ Basic Performance
1. **Upload medium-sized file** (1-5MB)
2. **Process document** with multiple pages
3. **Load dataset list** with multiple datasets
4. **Expected**:
   - [ ] Reasonable response times (<10s for uploads)
   - [ ] No browser freezing
   - [ ] Progress indicators work

---

## ✅ Final Verification

### ✅ Complete Workflow Test
1. **Login as admin**
2. **Upload CSV dataset**
3. **Upload document**
4. **Create share link**
5. **Access shared data**
6. **Use AI chat**
7. **Check analytics**
8. **Expected**: All steps work without errors

### ✅ System Health
- [ ] No console errors in browser
- [ ] Backend logs show no critical errors
- [ ] Database file size reasonable
- [ ] Memory usage stable

---

## 🛑 Stop Testing

### ✅ Cleanup
```bash
# Stop development environment
./stop-dev.sh

# Expected output:
# 🛑 Stopping AI Share Platform...
# ✅ All services stopped
```

---

## 📊 Test Results Summary

### ✅ Checklist Summary
- **Authentication**: ___/2 tests passed
- **Dataset Management**: ___/3 tests passed  
- **Data Connectors**: ___/2 tests passed
- **AI Integration**: ___/2 tests passed
- **Data Sharing**: ___/2 tests passed
- **Admin Panel**: ___/2 tests passed
- **Analytics**: ___/1 tests passed
- **Error Handling**: ___/1 tests passed
- **Responsive Design**: ___/1 tests passed
- **Performance**: ___/1 tests passed
- **Complete Workflow**: ___/1 tests passed

### ✅ Overall Status
- **Total Tests**: ___/17 passed
- **System Status**: ✅ Ready for Production / ⚠️ Needs Fixes / ❌ Major Issues

### 📝 Notes
```
Add any issues found during testing:

1. 

2. 

3. 
```

---

## 🎉 Success Criteria

The system is ready for production when:
- [ ] All automated tests pass (37/37 offline tests)
- [ ] All manual tests pass (17/17 checklist items)
- [ ] No critical errors in logs
- [ ] Performance is acceptable
- [ ] All core features work as expected

**🚀 Ready for Production Deployment!**